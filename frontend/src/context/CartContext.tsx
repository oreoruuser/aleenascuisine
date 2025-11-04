import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  type ReactNode,
} from "react";
import { upsertCart, type CartSnapshot, type CartTotals } from "../api/orders";

export interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  imageUrl?: string;
  notes?: string;
  addons?: Array<{ id: string; name: string; price: number }>;
  cartItemId?: string;
}

interface CartState {
  items: CartItem[];
  cartId?: string;
  cartToken?: string;
  totals?: CartTotals;
  syncing: boolean;
}

interface CartContextValue extends CartState {
  subtotal: number;
  grandTotal: number;
  itemCount: number;
  addItem: (item: CartItem) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clearCart: () => void;
  syncCart: (options?: { customerId?: string }) => Promise<CartSnapshot | undefined>;
}

const STORAGE_KEY = "aleenas.cart";

const initialState: CartState = {
  items: [],
  cartId: undefined,
  cartToken: undefined,
  totals: undefined,
  syncing: false,
};

type CartAction =
  | { type: "RESTORE"; payload: CartState }
  | { type: "ADD"; payload: CartItem }
  | { type: "REMOVE"; payload: string }
  | { type: "UPDATE_QUANTITY"; payload: { id: string; quantity: number } }
  | { type: "CLEAR" }
  | { type: "SYNCING"; payload: boolean }
  | { type: "APPLY_SERVER"; payload: { snapshot: CartSnapshot; mergedItems: CartItem[] } }
  | { type: "RESET_IDENTIFIERS" };

const cartReducer = (state: CartState, action: CartAction): CartState => {
  switch (action.type) {
    case "RESTORE":
      return { ...state, ...action.payload, syncing: false };
    case "ADD": {
      const item = action.payload;
      const existing = state.items.find((entry) => entry.id === item.id);
      const nextItems = existing
        ? state.items.map((entry) =>
            entry.id === item.id
              ? { ...entry, quantity: entry.quantity + item.quantity }
              : entry
          )
        : [...state.items, item];
      return { ...state, items: nextItems, totals: undefined };
    }
    case "REMOVE":
      return {
        ...state,
        items: state.items.filter((item) => item.id !== action.payload),
        totals: undefined,
      };
    case "UPDATE_QUANTITY": {
      const { id, quantity } = action.payload;
      const nextItems = state.items
        .map((item) => (item.id === id ? { ...item, quantity } : item))
        .filter((item) => item.quantity > 0);
      return { ...state, items: nextItems, totals: undefined };
    }
    case "CLEAR":
      return { items: [], cartId: undefined, cartToken: undefined, totals: undefined, syncing: false };
    case "SYNCING":
      return { ...state, syncing: action.payload };
    case "APPLY_SERVER": {
      const { snapshot, mergedItems } = action.payload;
      return {
        ...state,
        items: mergedItems,
        cartId: snapshot.cartId,
        cartToken: snapshot.cartToken,
        totals: snapshot.totals,
      };
    }
    case "RESET_IDENTIFIERS":
      return { ...state, cartId: undefined, cartToken: undefined, totals: undefined };
    default:
      return state;
  }
};

const readStoredCart = (): CartState => {
  if (typeof window === "undefined") {
    return initialState;
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
  return raw ? { ...initialState, ...(JSON.parse(raw) as CartState) } : initialState;
  } catch (error) {
    console.warn("Failed to parse stored cart", error);
    return initialState;
  }
};

const writeStoredCart = (state: CartState) => {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.warn("Failed to persist cart", error);
  }
};

const CartContext = createContext<CartContextValue | undefined>(undefined);

export const CartProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(cartReducer, initialState);

  useEffect(() => {
    const stored = readStoredCart();
    dispatch({ type: "RESTORE", payload: stored });
  }, []);

  useEffect(() => {
    writeStoredCart(state);
  }, [state]);

  const addItem = useCallback((item: CartItem) => {
    dispatch({ type: "ADD", payload: item });
  }, []);

  const removeItem = useCallback((id: string) => {
    dispatch({ type: "REMOVE", payload: id });
  }, []);

  const updateQuantity = useCallback((id: string, quantity: number) => {
    dispatch({ type: "UPDATE_QUANTITY", payload: { id, quantity } });
  }, []);

  const clearCart = useCallback(() => {
    dispatch({ type: "CLEAR" });
  }, []);

  const { items, cartToken } = state;

  const syncCart = useCallback(
    async (options?: { customerId?: string }) => {
      if (!items.length) {
        dispatch({ type: "RESET_IDENTIFIERS" });
        dispatch({ type: "SYNCING", payload: false });
        return undefined;
      }
      dispatch({ type: "SYNCING", payload: true });
      try {
        const snapshot = await upsertCart({
          customerId: options?.customerId,
          cartToken,
          items: items.map((item) => ({
            cakeId: item.id,
            quantity: item.quantity,
            priceEach: item.price,
          })),
        });
        const mergedItems: CartItem[] = snapshot.items.map((serverItem) => {
          const existing = items.find((cartItem) => cartItem.id === serverItem.cakeId);
          return {
            id: serverItem.cakeId,
            name: serverItem.name || existing?.name || "",
            price: serverItem.priceEach,
            quantity: serverItem.quantity,
            imageUrl: existing?.imageUrl,
            notes: existing?.notes,
            addons: existing?.addons,
            cartItemId: serverItem.cartItemId,
          };
        });
        dispatch({ type: "APPLY_SERVER", payload: { snapshot, mergedItems } });
        return snapshot;
      } catch (error) {
        console.warn("Failed to sync cart", error);
        return undefined;
      } finally {
        dispatch({ type: "SYNCING", payload: false });
      }
    },
    [items, cartToken]
  );

  const subtotal = useMemo(
    () => items.reduce((total, item) => total + item.price * item.quantity, 0),
    [items]
  );

  const grandTotal = state.totals?.total ?? subtotal;

  const itemCount = useMemo(
    () => items.reduce((total, item) => total + item.quantity, 0),
    [items]
  );

  const value = useMemo<CartContextValue>(
    () => ({
      ...state,
      subtotal,
      grandTotal,
      itemCount,
      addItem,
      removeItem,
      updateQuantity,
      clearCart,
      syncCart,
    }),
    [state, subtotal, grandTotal, itemCount, addItem, removeItem, updateQuantity, clearCart, syncCart]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

export const useCartContext = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCartContext must be used within a CartProvider");
  }
  return context;
};
