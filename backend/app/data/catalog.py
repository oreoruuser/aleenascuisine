"""Curated catalog entries for Aleena's Cuisine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CuratedCake:
    cake_id: str
    slug: str
    name: str
    description: str
    price: float
    currency: str
    category: str
    image_url: str
    stock_quantity: int = 24
    is_available: bool = True


CURATED_CAKES: tuple[CuratedCake, ...] = (
    CuratedCake(
        cake_id="midnight-cocoa-dream",
        slug="midnight-cocoa-dream",
        name="Midnight Cocoa Dream",
        description=(
            "Four decadent layers of Belgian dark chocolate sponge with a salted caramel truffle "
            "filling and gold-dusted ganache."
        ),
        price=1899,
        currency="INR",
        category="Signature",
        image_url="https://images.unsplash.com/photo-1505252907350-4291abb352f3?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="rose-pistachio",
        slug="rose-pistachio",
        name="Rose Pistachio Symphony",
        description=(
            "Persian saffron sponge layered with rose mousse, roasted pistachio praline, and edible rose petals."
        ),
        price=2099,
        currency="INR",
        category="Signature",
        image_url="https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="tropical-passion",
        slug="tropical-passion",
        name="Tropical Passion Mousse",
        description="A refreshing trio of mango, passionfruit, and coconut mousse on a macadamia sable base.",
        price=1699,
        currency="INR",
        category="Summer Specials",
        image_url="https://images.unsplash.com/photo-1522041319212-43697eababd2?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="strawberry-shortcake",
        slug="strawberry-shortcake",
        name="Strawberry Kyoto Shortcake",
        description=(
            "Japanese-style chiffon cake layered with whipped mascarpone, shiso syrup, and fresh handpicked strawberries."
        ),
        price=1799,
        currency="INR",
        category="Best Sellers",
        image_url="https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="lotus-biscoff",
        slug="lotus-biscoff",
        name="Lotus Biscoff Crunch",
        description="Caramel sponge with Biscoff cookie butter, toasted almonds, and a silky brown sugar buttercream.",
        price=1649,
        currency="INR",
        category="Best Sellers",
        image_url="https://images.unsplash.com/photo-1519869325930-281384150729?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="hazelnut-praline",
        slug="hazelnut-praline",
        name="Gianduja Hazelnut Praline",
        description="Layers of hazelnut dacquoise, milk chocolate cremeux, and crunchy feuillantine.",
        price=1995,
        currency="INR",
        category="Chocolate",
        image_url="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="opera-classique",
        slug="opera-classique",
        name="Opera Classique",
        description="Espresso-soaked almond joconde with dark chocolate ganache and coffee French buttercream.",
        price=1890,
        currency="INR",
        category="Chocolate",
        image_url="https://images.unsplash.com/photo-1534351590666-13e3e96b5017?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="pistachio-raspberry-entremet",
        slug="pistachio-raspberry-entremet",
        name="Pistachio Raspberry Entremet",
        description="Velvety pistachio bavarois with raspberry compote center and mirror glaze finish.",
        price=2149,
        currency="INR",
        category="Entremets",
        image_url="https://images.unsplash.com/photo-1527515637462-0f4c91ccd9ce?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="salted-caramel-eclair-cake",
        slug="salted-caramel-eclair-cake",
        name="Salted Caramel Eclair Cake",
        description="Choux pastry layers with Madagascar vanilla diplomat cream and burnt sugar caramel.",
        price=1725,
        currency="INR",
        category="Patisserie",
        image_url="https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="mango-tres-leches",
        slug="mango-tres-leches",
        name="Alphonso Mango Tres Leches",
        description="Saffron-infused tres leches with Alphonso mango pulp and kaffir lime chantilly.",
        price=1599,
        currency="INR",
        category="Summer Specials",
        image_url="https://images.unsplash.com/photo-1606313564200-e75d5e30476f?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="matcha-black-sesame",
        slug="matcha-black-sesame",
        name="Matcha Black Sesame Cloud",
        description="Uji matcha genoise with black sesame diplomat cream and yuzu jelly.",
        price=1675,
        currency="INR",
        category="Tea Cakes",
        image_url="https://images.unsplash.com/photo-1584118624012-df056829fbd0?auto=format&fit=crop&w=900&q=80",
    ),
    CuratedCake(
        cake_id="burnt-basque",
        slug="burnt-basque",
        name="San Sebastian Burnt Basque",
        description="Silky cream cheese cake with caramelized top, served with vanilla bean creme fraiche.",
        price=1549,
        currency="INR",
        category="Cheesecakes",
        image_url="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80",
    ),
)
