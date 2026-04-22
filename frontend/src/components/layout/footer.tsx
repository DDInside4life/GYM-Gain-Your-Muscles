export function Footer() {
  return (
    <footer className="mt-20 mb-6 px-4">
      <div className="glass-card mx-auto max-w-6xl p-6 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted">
        <div>© {new Date().getFullYear()} GYM — Gain Your Muscles</div>
        <div className="flex gap-4">
          <a href="#" className="hover:text-inherit">Terms</a>
          <a href="#" className="hover:text-inherit">Privacy</a>
          <a href="#" className="hover:text-inherit">Contact</a>
        </div>
      </div>
    </footer>
  );
}
