import { get, post } from "./client";

interface ServerRequestMetadata {
  request_id?: string;
  region?: string;
  api_version?: string;
}

interface ServerCakeSummary {
  cake_id: string;
  name: string;
  slug: string;
  price: number;
  currency: string;
  category?: string | null;
  is_available: boolean;
}

interface ServerCakeDetail extends ServerCakeSummary {
  description?: string | null;
  image_url?: string | null;
  stock_quantity: number;
  created_at: string;
  updated_at: string;
}

interface ServerPaginatedCakesResponse {
  cakes: ServerCakeSummary[];
  total_count: number;
  request: ServerRequestMetadata;
}

interface ServerCakeDetailResponse {
  cake: ServerCakeDetail;
  request: ServerRequestMetadata;
}

interface ServerCartItem {
  cart_item_id: string;
  cake_id: string;
  name?: string | null;
  quantity: number;
  price_each: number;
  line_total: number;
}

interface ServerCartTotals {
  subtotal: number;
  taxes: number;
  shipping: number;
  total: number;
}

interface ServerCartResponse {
  cart_id: string;
  customer_id?: string | null;
  cart_token?: string | null;
  items: ServerCartItem[];
  totals: ServerCartTotals;
  updated_at: string;
  request: ServerRequestMetadata;
}

interface ServerOrderDetail {
  order_id: string;
  order_total: number;
  currency: string;
  customer_id?: string | null;
  items: ServerCartItem[];
  totals: ServerCartTotals;
  payment_id?: string | null;
  payment_status: string;
  provider_order_id?: string | null;
  provider_payment_id?: string | null;
  idempotency_key?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  reservation_expires_at?: string | null;
  inventory_released: boolean;
  is_test: boolean;
  payment_is_test: boolean;
}

interface ServerOrderCreateResponse {
  order: ServerOrderDetail;
  provider_order_id: string;
  request: ServerRequestMetadata;
}

interface ServerOrderDetailResponse {
  order: ServerOrderDetail;
  request: ServerRequestMetadata;
}

export interface CakeSummary {
  id: string;
  name: string;
  slug: string;
  price: number;
  currency: string;
  category?: string;
  isAvailable: boolean;
}

export interface CakeDetail extends CakeSummary {
  description?: string;
  imageUrl?: string;
  stockQuantity: number;
  createdAt: string;
  updatedAt: string;
}

export interface CartLineItem {
  cartItemId: string;
  cakeId: string;
  name?: string;
  quantity: number;
  priceEach: number;
  lineTotal: number;
}

export interface CartTotals {
  subtotal: number;
  taxes: number;
  shipping: number;
  total: number;
}

export interface CartSnapshot {
  cartId: string;
  cartToken?: string;
  customerId?: string;
  items: CartLineItem[];
  totals: CartTotals;
  updatedAt: string;
}

export interface CartUpsertPayload {
  customerId?: string;
  cartToken?: string;
  items: Array<{
    cakeId: string;
    quantity: number;
    priceEach: number;
  }>;
}

export interface OrderDetail {
  orderId: string;
  status: string;
  paymentStatus: string;
  orderTotal: number;
  currency: string;
  customerId?: string;
  items: CartLineItem[];
  totals: CartTotals;
  providerOrderId?: string;
  providerPaymentId?: string;
  paymentId?: string;
  idempotencyKey?: string;
  createdAt: string;
  updatedAt: string;
  reservationExpiresAt?: string;
  inventoryReleased: boolean;
  isTest: boolean;
  paymentIsTest: boolean;
}

export interface OrderCreatePayload {
  cartId: string;
  customerId?: string;
  idempotencyKey: string;
  isTest?: boolean;
}

export interface OrderCreateResult {
  order: OrderDetail;
  providerOrderId: string;
}

const mapCakeSummary = (cake: ServerCakeSummary): CakeSummary => ({
  id: cake.cake_id,
  name: cake.name,
  slug: cake.slug,
  price: cake.price,
  currency: cake.currency,
  category: cake.category ?? undefined,
  isAvailable: cake.is_available,
});

const mapCakeDetail = (cake: ServerCakeDetail): CakeDetail => ({
  ...mapCakeSummary(cake),
  description: cake.description ?? undefined,
  imageUrl: cake.image_url ?? undefined,
  stockQuantity: cake.stock_quantity,
  createdAt: cake.created_at,
  updatedAt: cake.updated_at,
});

const mapCartLine = (item: ServerCartItem): CartLineItem => ({
  cartItemId: item.cart_item_id,
  cakeId: item.cake_id,
  name: item.name ?? undefined,
  quantity: item.quantity,
  priceEach: item.price_each,
  lineTotal: item.line_total,
});

const mapTotals = (totals: ServerCartTotals): CartTotals => ({
  subtotal: totals.subtotal,
  taxes: totals.taxes,
  shipping: totals.shipping,
  total: totals.total,
});

const mapCart = (payload: ServerCartResponse): CartSnapshot => ({
  cartId: payload.cart_id,
  cartToken: payload.cart_token ?? undefined,
  customerId: payload.customer_id ?? undefined,
  items: payload.items.map(mapCartLine),
  totals: mapTotals(payload.totals),
  updatedAt: payload.updated_at,
});

const mapOrderDetail = (payload: ServerOrderDetail): OrderDetail => ({
  orderId: payload.order_id,
  status: payload.status,
  paymentStatus: payload.payment_status,
  orderTotal: payload.order_total,
  currency: payload.currency,
  customerId: payload.customer_id ?? undefined,
  items: payload.items.map(mapCartLine),
  totals: mapTotals(payload.totals),
  providerOrderId: payload.provider_order_id ?? undefined,
  providerPaymentId: payload.provider_payment_id ?? undefined,
  paymentId: payload.payment_id ?? undefined,
  idempotencyKey: payload.idempotency_key ?? undefined,
  createdAt: payload.created_at,
  updatedAt: payload.updated_at,
  reservationExpiresAt: payload.reservation_expires_at ?? undefined,
  inventoryReleased: payload.inventory_released,
  isTest: payload.is_test,
  paymentIsTest: payload.payment_is_test,
});

const normalizeCartPayload = (payload: CartUpsertPayload) => ({
  customer_id: payload.customerId ?? null,
  cart_token: payload.cartToken ?? null,
  items: payload.items.map((item) => ({
    cake_id: item.cakeId,
    quantity: item.quantity,
    price_each: item.priceEach,
  })),
});

const normalizeOrderPayload = (payload: OrderCreatePayload) => ({
  idempotency_key: payload.idempotencyKey,
  cart_id: payload.cartId,
  customer_id: payload.customerId ?? null,
  is_test: payload.isTest ?? null,
});

export const fetchMenu = async (): Promise<CakeSummary[]> => {
  const response = await get<ServerPaginatedCakesResponse>("/cakes");
  return response.cakes.map(mapCakeSummary);
};

export const fetchMenuItem = async (id: string): Promise<CakeDetail> => {
  const response = await get<ServerCakeDetailResponse>(`/cakes/${id}`);
  return mapCakeDetail(response.cake);
};

export const upsertCart = async (payload: CartUpsertPayload): Promise<CartSnapshot> => {
  const response = await post<ServerCartResponse>("/cart", normalizeCartPayload(payload));
  return mapCart(response);
};

export const fetchCart = async (reference: string): Promise<CartSnapshot> => {
  const response = await get<ServerCartResponse>(`/cart/${reference}`);
  return mapCart(response);
};

export const createOrder = async (
  payload: OrderCreatePayload
): Promise<OrderCreateResult> => {
  const response = await post<ServerOrderCreateResponse>("/orders", normalizeOrderPayload(payload));
  return {
    order: mapOrderDetail(response.order),
    providerOrderId: response.provider_order_id,
  };
};

export const fetchOrder = async (orderId: string): Promise<OrderDetail> => {
  const response = await get<ServerOrderDetailResponse>(`/orders/${orderId}`);
  return mapOrderDetail(response.order);
};
