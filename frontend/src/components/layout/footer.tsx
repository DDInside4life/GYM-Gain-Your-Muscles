import { Instagram, Send, Youtube } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-20 mb-6 px-4">
      <div className="glass-card mx-auto max-w-6xl px-6 py-5 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted">
        <div>© {new Date().getFullYear()} GYM — Gain Your Muscles</div>
        <div className="flex items-center gap-5">
          <a href="#" className="hover:text-inherit transition">Политика конфиденциальности</a>
          <a href="#" className="hover:text-inherit transition">Условия использования</a>
        </div>
        <div className="flex items-center gap-3 text-muted">
          <a href="#" aria-label="Instagram" className="hover:text-brand-500 dark:hover:text-violet-300 transition"><Instagram size={16} /></a>
          <a href="#" aria-label="Telegram" className="hover:text-brand-500 dark:hover:text-violet-300 transition"><Send size={16} /></a>
          <a href="#" aria-label="YouTube" className="hover:text-brand-500 dark:hover:text-violet-300 transition"><Youtube size={16} /></a>
        </div>
      </div>
    </footer>
  );
}
