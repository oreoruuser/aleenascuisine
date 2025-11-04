import { Link } from "react-router-dom";
import { curatedCakes } from "../data/cakes";

const spotlight = curatedCakes.slice(0, 3);

export const HomePage = () => (
  <main className="home">
    <section className="hero hero--home">
      <div className="hero__content">
        <span className="eyebrow">Aleena&apos;s Patisserie</span>
        <h1>Celebrate every milestone with couture cakes</h1>
        <p>
          Bespoke cakes crafted to order with layered textures, slow-baked sponges, and hand-piped finishes. We partner
          with local farmers and source couverture chocolate to create unforgettable centrepieces for your celebrations.
        </p>
        <div className="hero__actions">
          <Link to="/menu" className="button button--primary">
            Explore the cake studio
          </Link>
          <Link to="/profile" className="button button--ghost">
            Meet your pastry chef
          </Link>
        </div>
        <dl className="hero__metrics">
          <div>
            <dt>500+ bespoke cakes</dt>
            <dd>Hand-delivered across Kochi &amp; Bengaluru</dd>
          </div>
          <div>
            <dt>48-hour preorder window</dt>
            <dd>Flexible rush options for intimate gatherings</dd>
          </div>
          <div>
            <dt>Premium ingredients</dt>
            <dd>Valrhona cacao, seasonal fruit, and single-origin vanilla</dd>
          </div>
        </dl>
      </div>
      <div className="hero__gallery">
        {spotlight.map((cake) => (
          <figure key={cake.id} className="hero__tile">
            <img src={cake.imageUrl} alt={cake.name} loading="lazy" />
            <figcaption>
              <strong>{cake.name}</strong>
              <span>{cake.category}</span>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>

    <section className="home__services">
      <article>
        <h2>Consultation-driven design</h2>
        <p>
          Share your theme, flavour notes, and guest list. We sketch out concepts, mock up palettes, and customise
          textures so your cake feels unique to the celebration.
        </p>
      </article>
      <article>
        <h2>Chef-led tastings</h2>
        <p>
          Book an intimate tasting flight at our kitchen studio. Sample seasonal mousse, sponge, and glaze pairings and
          finalise your menu in one sitting.
        </p>
      </article>
      <article>
        <h2>White-glove delivery</h2>
        <p>
          Climate-controlled vehicles and on-site styling ensure your cake arrives picture-perfect. Setup includes florals
          and dessert table curation on request.
        </p>
      </article>
    </section>
  </main>
);
