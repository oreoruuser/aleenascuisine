import type { CakeSummary } from "../api/orders";

export interface CuratedCake extends CakeSummary {
  description: string;
  imageUrl: string;
}

const price = (amount: number) => ({
  price: amount,
  currency: "INR" as const,
});

export const curatedCakes: CuratedCake[] = [
  {
    id: "midnight-cocoa-dream",
    slug: "midnight-cocoa-dream",
    name: "Midnight Cocoa Dream",
    description: "Four decadent layers of Belgian dark chocolate sponge with a salted caramel truffle filling and gold-dusted ganache.",
    imageUrl:
      "https://images.unsplash.com/photo-1505252907350-4291abb352f3?auto=format&fit=crop&w=900&q=80",
    category: "Signature",
    isAvailable: true,
    ...price(1899),
  },
  {
    id: "rose-pistachio",
    slug: "rose-pistachio",
    name: "Rose Pistachio Symphony",
    description: "Persian saffron sponge layered with rose mousse, roasted pistachio praline, and edible rose petals.",
    imageUrl:
      "https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?auto=format&fit=crop&w=900&q=80",
    category: "Signature",
    isAvailable: true,
    ...price(2099),
  },
  {
    id: "tropical-passion",
    slug: "tropical-passion",
    name: "Tropical Passion Mousse",
    description: "A refreshing trio of mango, passionfruit, and coconut mousse on a macadamia sable base.",
    imageUrl:
      "https://images.unsplash.com/photo-1522041319212-43697eababd2?auto=format&fit=crop&w=900&q=80",
    category: "Summer Specials",
    isAvailable: true,
    ...price(1699),
  },
  {
    id: "strawberry-shortcake",
    slug: "strawberry-shortcake",
    name: "Strawberry Kyoto Shortcake",
    description: "Japanese-style chiffon cake layered with whipped mascarpone, shiso syrup, and fresh handpicked strawberries.",
    imageUrl:
      "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=900&q=80",
    category: "Best Sellers",
    isAvailable: true,
    ...price(1799),
  },
  {
    id: "lotus-biscoff",
    slug: "lotus-biscoff",
    name: "Lotus Biscoff Crunch",
    description: "Caramel sponge with Biscoff cookie butter, toasted almonds, and a silky brown sugar buttercream.",
    imageUrl:
      "https://images.unsplash.com/photo-1519869325930-281384150729?auto=format&fit=crop&w=900&q=80",
    category: "Best Sellers",
    isAvailable: true,
    ...price(1649),
  },
  {
    id: "hazelnut-praline",
    slug: "hazelnut-praline",
    name: "Gianduja Hazelnut Praline",
    description: "Layers of hazelnut dacquoise, milk chocolate crémeux, and crunchy feuillantine.",
    imageUrl:
      "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80",
    category: "Chocolate",
    isAvailable: true,
    ...price(1995),
  },
  {
    id: "opera-classique",
    slug: "opera-classique",
    name: "Opéra Classique",
    description: "Espresso-soaked almond joconde with dark chocolate ganache and coffee French buttercream.",
    imageUrl:
      "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?auto=format&fit=crop&w=900&q=80",
    category: "Chocolate",
    isAvailable: true,
    ...price(1890),
  },
  {
    id: "pistachio-raspberry-entremet",
    slug: "pistachio-raspberry-entremet",
    name: "Pistachio Raspberry Entremet",
    description: "Velvety pistachio bavarois with raspberry compote center and mirror glaze finish.",
    imageUrl:
      "https://images.unsplash.com/photo-1527515637462-0f4c91ccd9ce?auto=format&fit=crop&w=900&q=80",
    category: "Entremets",
    isAvailable: true,
    ...price(2149),
  },
  {
    id: "salted-caramel-eclair-cake",
    slug: "salted-caramel-eclair-cake",
    name: "Salted Caramel Éclair Cake",
    description: "Choux pastry layers with Madagascar vanilla diplomat cream and burnt sugar caramel.",
    imageUrl:
      "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?auto=format&fit=crop&w=900&q=80",
  category: "Patisserie",
    isAvailable: true,
    ...price(1725),
  },
  {
    id: "mango-tres-leches",
    slug: "mango-tres-leches",
    name: "Alphonso Mango Tres Leches",
    description: "Saffron-infused tres leches with Alphonso mango pulp and kaffir lime chantilly.",
    imageUrl:
      "https://images.unsplash.com/photo-1606313564200-e75d5e30476f?auto=format&fit=crop&w=900&q=80",
    category: "Summer Specials",
    isAvailable: true,
    ...price(1599),
  },
  {
    id: "matcha-black-sesame",
    slug: "matcha-black-sesame",
    name: "Matcha Black Sesame Cloud",
    description: "Uji matcha genoise with black sesame diplomat cream and yuzu jelly.",
    imageUrl:
      "https://images.unsplash.com/photo-1584118624012-df056829fbd0?auto=format&fit=crop&w=900&q=80",
    category: "Tea Cakes",
    isAvailable: true,
    ...price(1675),
  },
  {
    id: "burnt-basque",
    slug: "burnt-basque",
    name: "San Sebastián Burnt Basque",
    description: "Silky cream cheese cake with caramelized top, served with vanilla bean crème fraîche.",
    imageUrl:
      "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80",
    category: "Cheesecakes",
    isAvailable: true,
    ...price(1549),
  }
];
