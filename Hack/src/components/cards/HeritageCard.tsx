import { motion } from "framer-motion";

interface Site {
  id: string;
  name: string;
  location: string;
  year?: string;
  description: string;
  image: string;
}

interface Props {
  site: Site;
}

export default function HeritageCard({ site }: Props) {
  return (
    <motion.article
      whileHover={{ y: -4 }}
      className="group glass overflow-hidden rounded-xl cursor-pointer"
    >
      <div className="aspect-[4/3] overflow-hidden bg-heritage-elevated">
        <img
          src={site.image}
          alt={site.name}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-heritage-deep/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      </div>
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-editorial text-lg text-ink-primary group-hover:text-accent-gold transition-colors">
            {site.name}
          </h3>
          {site.year && (
            <span className="font-display text-[11px] text-ink-muted whitespace-nowrap border border-line px-2 py-0.5 rounded-full">
              {site.year}
            </span>
          )}
        </div>
        <p className="text-sm text-ink-secondary mt-1.5 leading-relaxed line-clamp-2">
          {site.description}
        </p>
        <p className="mt-3 text-xs text-ink-muted">{site.location}</p>
      </div>
    </motion.article>
  );
}