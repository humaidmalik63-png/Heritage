export default function SkipLink() {
  return (
    <a
      href="#main"
      className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-accent-gold focus:text-heritage-deep focus:font-semibold focus:shadow-gold"
    >
      Skip to main content
    </a>
  );
}