import { useEffect, useState } from "react";
import type { Catalogue } from "../types/catalogue";
import { fetchCatalogue } from "../api/catalog";
import Hero from "../components/Hero";
import Row from "../components/Row";
import StateBlock from "../components/StateBlock";

export default function Home() {
  const [catalogue, setCatalogue] = useState<Catalogue | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCatalogue().then(setCatalogue).catch(() => setError("failed"));
  }, []);

  if (error) {
    return (
      <div className="container">
        <StateBlock
          title="Peblo TV is taking a nap"
          subtitle="We couldn't load any shows right now. Try again in a moment!"
        />
      </div>
    );
  }

  if (!catalogue) {
    return (
      <div className="container">
        <StateBlock title="Getting your shows ready..." />
      </div>
    );
  }

  const allShows = catalogue.sections.flatMap((s) => s.shows);
  const featured = allShows[0];

  if (!featured) {
    return (
      <div className="container">
        <StateBlock
          title="No shows here yet"
          subtitle="Check back soon — new adventures are on the way!"
        />
      </div>
    );
  }

  return (
    <div className="container">
      <Hero show={featured} />
      {catalogue.sections.map((section) => (
        <Row key={section.section} title={section.section} shows={section.shows} />
      ))}
    </div>
  );
}
