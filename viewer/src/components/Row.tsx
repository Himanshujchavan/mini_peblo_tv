import type { CatalogueShow } from "../types/catalogue";
import ShowCard from "./ShowCard";
import { categoryColor } from "./util";

export default function Row({ title, shows }: { title: string; shows: CatalogueShow[] }) {
  if (shows.length === 0) return null;
  const dotColor = categoryColor(shows[0].categories);

  return (
    <section className="row-section">
      <h2 className="row-heading">
        <span className="row-dot" style={{ background: dotColor }} aria-hidden="true" />
        {title}
      </h2>
      <div className="row-scroller">
        {shows.map((show) => (
          <ShowCard
            key={show.show_id}
            id={show.show_id}
            title={show.title}
            imageUrl={show.artwork.poster?.url}
          />
        ))}
      </div>
    </section>
  );
}
