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
  },
  {
    id: "cardamom-honey-praline",
    slug: "cardamom-honey-praline",
    name: "Cardamom Honey Praline",
    description: "Fragrant cardamom sponge layered with acacia honey mousse and cashew praline crunch.",
    imageUrl:
      "https://images.unsplash.com/photo-1519866663826-ff6205d0f3c4?auto=format&fit=crop&w=900&q=80",
    category: "Signature",
    isAvailable: true,
    ...price(1825),
  },
  {
    id: "saffron-kheer-entremet",
    slug: "saffron-kheer-entremet",
    name: "Saffron Kheer Entremet",
    description: "Layers of saffron rice pudding mousse with pistachio financier and rosewater gelée.",
    imageUrl:
      "https://images.unsplash.com/photo-1529651737248-dad5e287768e?auto=format&fit=crop&w=900&q=80",
    category: "Entremets",
    isAvailable: true,
    ...price(2195),
  },
  {
    id: "black-forest-reimagined",
    slug: "black-forest-reimagined",
    name: "Black Forest Reimagined",
    description: "Kirsch-soaked chocolate sponge with cherry compote, vanilla chantilly, and dark chocolate shards.",
    imageUrl:
      "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80",
    category: "Chocolate",
    isAvailable: true,
    ...price(1760),
  },
  {
    id: "orange-blossom-chantilly",
    slug: "orange-blossom-chantilly",
    name: "Orange Blossom Chantilly",
    description: "Olive oil citrus sponge with orange blossom mascarpone and candied peel.",
    imageUrl:
      "https://images.unsplash.com/photo-1464349153735-7db50ed83c84?auto=format&fit=crop&w=900&q=80",
    category: "Signature",
    isAvailable: true,
    ...price(1680),
  },
  {
    id: "blueberry-lavender-crepe",
    slug: "blueberry-lavender-crepe",
    name: "Blueberry Lavender Mille Crêpe",
    description: "Twenty layers of crêpes with blueberry diplomat cream and lavender honey glaze.",
    imageUrl:
      "https://images.unsplash.com/photo-1544378331-41c00ad39009?auto=format&fit=crop&w=900&q=80",
    category: "Patisserie",
    isAvailable: true,
    ...price(1895),
  },
  {
    id: "masala-chai-tiramisu",
    slug: "masala-chai-tiramisu",
    name: "Masala Chai Tiramisu",
    description: "Espresso-soaked ladyfingers layered with chai mascarpone and jaggery caramel.",
    imageUrl:
      "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=900&q=80",
    category: "Best Sellers",
    isAvailable: true,
    ...price(1720),
  },
  {
    id: "lemongrass-ginger-silk",
    slug: "lemongrass-ginger-silk",
    name: "Lemongrass Ginger Silk",
    description: "Lemongrass-infused mousse with ginger crunch and coconut dacquoise base.",
    imageUrl:
      "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=900&q=80",
    category: "Summer Specials",
    isAvailable: true,
    ...price(1650),
  },
  {
    id: "raspberry-choux-tower",
    slug: "raspberry-choux-tower",
    name: "Raspberry Choux Tower",
    description: "Profiterole tower filled with raspberry crème légère and white chocolate glaze.",
    imageUrl:
      "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=900&q=80",
    category: "Patisserie",
    isAvailable: true,
    ...price(2060),
  },
  {
    id: "coconut-lychee-pavlova",
    slug: "coconut-lychee-pavlova",
    name: "Coconut Lychee Pavlova",
    description: "Crisp meringue with coconut diplomat cream, lychee pearls, and tropical fruits.",
    imageUrl:
      "https://images.unsplash.com/photo-1475856034135-1f1398359159?auto=format&fit=crop&w=900&q=80",
    category: "Summer Specials",
    isAvailable: true,
    ...price(1580),
  },
  {
    id: "toasted-almond-frangipane",
    slug: "toasted-almond-frangipane",
    name: "Toasted Almond Frangipane",
    description: "Roasted almond frangipane tart with apricot compote and vanilla bean crème.",
    imageUrl:
      "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80",
    category: "Tea Cakes",
    isAvailable: true,
    ...price(1620),
  },
  {
    id: "pistachio-kulfi-semifreddo",
    slug: "pistachio-kulfi-semifreddo",
    name: "Pistachio Kulfi Semifreddo",
    description: "Kulfi-inspired semifreddo with pistachio nougatine and saffron white chocolate glaze.",
    imageUrl:
      "https://images.unsplash.com/photo-1546069901-eacef0df6022?auto=format&fit=crop&w=900&q=80",
    category: "Signature",
    isAvailable: true,
    ...price(1880),
  },
  {
    id: "espresso-dulce-dome",
    slug: "espresso-dulce-dome",
    name: "Espresso Dulce Dome",
    description: "Espresso mousse dome with dulce de leche core and chocolate sable base.",
    imageUrl:
      "https://images.unsplash.com/photo-1549571936-20ef4d8d08f1?auto=format&fit=crop&w=900&q=80",
    category: "Chocolate",
    isAvailable: true,
    ...price(1985),
  },
  {
    id: "ruby-grapefruit-olive-oil",
    slug: "ruby-grapefruit-olive-oil",
    name: "Ruby Grapefruit Olive Oil Cake",
    description: "Mediterranean olive oil loaf with ruby grapefruit glaze and candied zest.",
    imageUrl:
      "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80",
    category: "Tea Cakes",
    isAvailable: true,
    ...price(1495),
  },
  {
    id: "spiced-pear-financier",
    slug: "spiced-pear-financier",
    name: "Spiced Pear Financier",
    description: "Brown butter financier topped with mulled wine poached pears and almond crumble.",
    imageUrl:
      "https://images.unsplash.com/photo-1530669721897-dc85f86be1d5?auto=format&fit=crop&w=900&q=80",
    category: "Patisserie",
    isAvailable: true,
    ...price(1560),
  },
];
