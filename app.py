
import sys, os, threading, queue, webbrowser, json
from datetime import datetime, timedelta
from tkinter import filedialog as fd
import customtkinter as ctk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from mvf.runner_next import run_next
from mvf.recents import list_recents, add_recent, clear_recents
from mvf.multi import run_multi, ATHLETES_PATH

def _plus4_time_str(date_ymd: str, hhmm: str) -> str:
    try:
        dt = datetime.strptime(f"{date_ymd} {hhmm}", "%Y-%m-%d %H:%M")
        dt2 = dt + timedelta(hours=3)
        return dt2.strftime("%H:%M")
    except Exception:
        return ""

def safe_int(value, default):
    try:
        return int(value)
    except Exception:
        return default

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("Match Video Finder — Próximos Jogos & Agenda Multi")
        self.geometry("1080x700")
        self.minsize(900, 600)

        self.q = queue.Queue()
        self._recent_items = []
        self.last_multi = None

        self.tab = ctk.CTkTabview(self)
        self.tab.pack(fill="both", expand=True, padx=12, pady=12)

        self.tab.add("Único time")
        self.tab.add("Agenda (multi)")

        self._build_single(self.tab.tab("Único time"))
        self._build_multi(self.tab.tab("Agenda (multi)"))

        self.after(100, self._tick)

    # ------------- Aba Single -------------
    def _build_single(self, parent):
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        self.left = ctk.CTkFrame(parent, corner_radius=12)
        self.left.grid(row=0, column=0, sticky="nsw", padx=12, pady=12)

        self.right = ctk.CTkFrame(parent, corner_radius=12)
        self.right.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        self.right.grid_columnconfigure(0, weight=1)
        self.right.grid_rowconfigure(1, weight=1)

        self._build_left_single()
        self._build_right_single()

        self._refresh_recents_menu()

    def _build_left_single(self):
        pad = {"padx": 10, "pady": 6}
        ctk.CTkLabel(self.left, text="⚽ Próximos Jogos (único time)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, **pad)

        ctk.CTkLabel(self.left, text="Time (nome)").grid(row=1, column=0, sticky="w", **pad)
        self.team_entry = ctk.CTkEntry(self.left, placeholder_text='ex.: "Benfica Futsal"')
        self.team_entry.grid(row=2, column=0, columnspan=2, sticky="ew", **pad)

        ctk.CTkLabel(self.left, text="ID do time (SofaScore)").grid(row=3, column=0, sticky="w", **pad)
        self.team_id_entry = ctk.CTkEntry(self.left, placeholder_text="ex.: 306038")
        self.team_id_entry.grid(row=4, column=0, columnspan=2, sticky="ew", **pad)

        ctk.CTkLabel(self.left, text="URL do time (SofaScore)").grid(row=5, column=0, sticky="w", **pad)
        self.team_url_entry = ctk.CTkEntry(self.left, placeholder_text="https://www.sofascore.com/.../team/.../ID")
        self.team_url_entry.grid(row=6, column=0, columnspan=2, sticky="ew", **pad)

        ctk.CTkLabel(self.left, text="Qtd. próximos jogos").grid(row=7, column=0, sticky="w", **pad)
        self.next_entry = ctk.CTkEntry(self.left)
        self.next_entry.insert(0, "3")
        self.next_entry.grid(row=8, column=0, columnspan=2, sticky="ew", **pad)

        ctk.CTkLabel(self.left, text="Fuso horário").grid(row=9, column=0, sticky="w", **pad)
        self.tz_entry = ctk.CTkEntry(self.left)
        self.tz_entry.insert(0, "America/Fortaleza")
        self.tz_entry.grid(row=10, column=0, columnspan=2, sticky="ew", **pad)

        self.btn = ctk.CTkButton(self.left, text="Buscar próximos", command=self.on_search_single)
        self.btn.grid(row=11, column=0, columnspan=2, sticky="ew", padx=10, pady=(12, 6))

        self.pb = ctk.CTkProgressBar(self.left, mode="indeterminate")
        self.pb.grid(row=12, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))
        self.pb.stop()

        self.status = ctk.CTkLabel(self.left, text="", text_color="#9aa4b2")
        self.status.grid(row=13, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10))

        ctk.CTkLabel(self.left, text="Recentes").grid(row=14, column=0, sticky="w", **pad)
        self.recents_menu = ctk.CTkOptionMenu(self.left, values=["(vazio)"], command=lambda _: None)
        self.recents_menu.set("(vazio)")
        self.recents_menu.grid(row=15, column=0, sticky="ew", **pad)

        self.use_recent_btn = ctk.CTkButton(self.left, text="Usar selecionado", command=self._apply_recent, width=140)
        self.use_recent_btn.grid(row=15, column=1, sticky="ew", **pad)

        self.clear_recent_btn = ctk.CTkButton(self.left, text="Limpar lista", command=self._clear_recents, fg_color="#7c2d12")
        self.clear_recent_btn.grid(row=16, column=0, columnspan=2, sticky="ew", **pad)

    def _build_right_single(self):
        self.meta = ctk.CTkLabel(self.right, text="", anchor="w")
        self.meta.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))

        self.scroll = ctk.CTkScrollableFrame(self.right, corner_radius=10)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.scroll.grid_columnconfigure(0, weight=1)

        self.empty = ctk.CTkLabel(self.right, text="Sem próximos jogos.", text_color="#9aa4b2")
        self.empty.grid(row=2, column=0, padx=8, pady=(0,8))
        self.empty.grid_remove()

    def _refresh_recents_menu(self):
        self._recent_items = list_recents()
        if not self._recent_items:
            self.recents_menu.configure(values=["(vazio)"])
            self.recents_menu.set("(vazio)")
            return
        labels = [f"{i.get('name') or 'sofascore:'+str(i.get('team_id'))} (ID: {i.get('team_id') or '-'})" for i in self._recent_items]
        self.recents_menu.configure(values=labels)
        self.recents_menu.set(labels[0])

    def _apply_recent(self):
        if not self._recent_items:
            return
        current = self.recents_menu.get()
        try:
            idx = [f"{i.get('name') or 'sofascore:'+str(i.get('team_id'))} (ID: {i.get('team_id') or '-'})" for i in self._recent_items].index(current)
        except ValueError:
            idx = 0
        it = self._recent_items[idx]
        self.team_entry.delete(0, "end")
        self.team_entry.insert(0, it.get("name") or "")
        self.team_id_entry.delete(0, "end")
        self.team_id_entry.insert(0, str(it.get("team_id") or ""))
        self.team_url_entry.delete(0, "end")
        self.team_url_entry.insert(0, it.get("url") or "")

    def _clear_recents(self):
        clear_recents()
        self._refresh_recents_menu()

    def on_search_single(self):
        team = self.team_entry.get().strip()
        team_id = self.team_id_entry.get().strip()
        team_url = self.team_url_entry.get().strip()
        nxt = safe_int(self.next_entry.get(), 3)
        tz = self.tz_entry.get().strip() or "America/Fortaleza"

        payload = {
            "team": team or None,
            "team_id": safe_int(team_id, None) if team_id else None,
            "team_url": team_url or None,
            "next": nxt,
            "tz": tz,
        }

        self._set_loading_single(True, "Buscando próximos jogos…")
        self._clear_results_single()
        threading.Thread(target=self._worker_single, args=(payload,), daemon=True).start()

    def _worker_single(self, payload: dict):
        try:
            data = run_next(
                team=payload["team"],
                limit=payload["next"],
                tz=payload["tz"],
                team_id=payload["team_id"],
                team_url=payload["team_url"],
            )
            add_recent(payload["team"], payload["team_id"], payload["team_url"])
            self.q.put(("ok_single", data))
        except Exception as e:
            self.q.put(("err_single", str(e)))

    def _set_loading_single(self, flag: bool, msg: str = ""):
        if flag:
            self.btn.configure(state="disabled", text="Buscando…")
            self.pb.start()
            self.status.configure(text=msg)
        else:
            self.btn.configure(state="normal", text="Buscar próximos")
            self.pb.stop()
            self.status.configure(text=msg)

    def _clear_results_single(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.meta.configure(text="")
        self.empty.grid_remove()

    def _render_single(self, data: dict):
        self.meta.configure(text=f"Atualizado: {data.get('checked_at','—')} | Time: {data.get('team','—')}")
        items = data.get("upcoming") or []
        if not items:
            self.empty.grid()
            return
        for i, m in enumerate(items):
            self._add_card_single(i, m)

    def _add_card_single(self, idx: int, m: dict):
        f = ctk.CTkFrame(self.scroll, corner_radius=12, fg_color="#171a21")
        f.grid(row=idx, column=0, sticky="ew", padx=8, pady=6)
        f.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(f, text=f"{m.get('home','')}  x  {m.get('away','')}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        title.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,2))
        sub = f"{m.get('tournament','')}  —  {m.get('date_local','')}  {m.get('time_local','')}  |  PT: {_plus4_time_str(m.get('date_local',''), m.get('time_local',''))}"
        ctk.CTkLabel(f, text=sub, text_color="#9aa4b2", anchor="w").grid(row=1, column=0, sticky="ew", padx=10, pady=(0,8))
        def open_event():
            url = m.get("event_url")
            if url:
                webbrowser.open_new_tab(url)
        ctk.CTkButton(f, text="Abrir no SofaScore", command=open_event, width=160).grid(row=0, column=1, rowspan=2, padx=10, pady=10)

    # ------------- Aba Multi -------------
    def _build_multi(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(parent, corner_radius=12)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,6))
        top.grid_columnconfigure(6, weight=1)

        ctk.CTkLabel(top, text="📅 Agenda (multi atletas)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(top, text="Qtd. próximos por atleta").grid(row=1, column=0, padx=10, pady=6, sticky="w")
        self.n_multi = ctk.CTkEntry(top, width=120)
        self.n_multi.insert(0, "2")
        self.n_multi.grid(row=1, column=1, padx=10, pady=6, sticky="w")

        ctk.CTkLabel(top, text="Fuso horário").grid(row=1, column=2, padx=10, pady=6, sticky="w")
        self.tz_multi = ctk.CTkEntry(top, width=200)
        self.tz_multi.insert(0, "America/Fortaleza")
        self.tz_multi.grid(row=1, column=3, padx=10, pady=6, sticky="w")

        self.btn_multi = ctk.CTkButton(top, text="Buscar agenda", command=self.on_search_multi, width=160)
        self.btn_multi.grid(row=1, column=4, padx=10, pady=6, sticky="e")

        def open_athletes():
            path = os.path.join(BASE_DIR, "config", "athletes.json")
            try:
                if os.name == "nt":
                    os.startfile(path)  # Windows
                else:
                    import subprocess, sys
                    subprocess.Popen(["open" if sys.platform=="darwin" else "xdg-open", path])
            except Exception:
                webbrowser.open_new_tab("file://" + path.replace("\\\\","/"))
        ctk.CTkButton(top, text="Abrir athletes.json", command=open_athletes, width=160).grid(row=1, column=5, padx=10, pady=6)

        self.btn_export = ctk.CTkButton(top, text="Exportar TXT", command=self.on_export_multi, width=140)
        self.btn_export.grid(row=1, column=6, padx=10, pady=6, sticky="e")

        self.pb_multi = ctk.CTkProgressBar(top, mode="indeterminate")
        self.pb_multi.grid(row=2, column=0, columnspan=7, sticky="ew", padx=10, pady=(0,6))
        self.pb_multi.stop()

        self.status_multi = ctk.CTkLabel(top, text="", text_color="#9aa4b2")
        self.status_multi.grid(row=3, column=0, columnspan=7, sticky="w", padx=10, pady=(0, 4))

        self.scroll_multi = ctk.CTkScrollableFrame(parent, corner_radius=10)
        self.scroll_multi.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        self.scroll_multi.grid_columnconfigure(0, weight=1)

    def on_search_multi(self):
        nxt = safe_int(self.n_multi.get(), 2)
        tz = self.tz_multi.get().strip() or "America/Fortaleza"
        self._set_loading_multi(True, "Buscando agenda…")
        self._clear_multi()
        threading.Thread(target=self._worker_multi, args=(nxt, tz), daemon=True).start()

    def _worker_multi(self, nxt, tz):
        try:
            data = run_multi(next_per_team=nxt, tz=tz)
            self.q.put(("ok_multi", data))
        except Exception as e:
            self.q.put(("err_multi", str(e)))

    def _set_loading_multi(self, flag: bool, msg: str = ""):
        if flag:
            self.btn_multi.configure(state="disabled", text="Buscando…")
            self.pb_multi.start()
            self.status_multi.configure(text=msg)
        else:
            self.btn_multi.configure(state="normal", text="Buscar agenda")
            self.pb_multi.stop()
            self.status_multi.configure(text=msg)

    def _clear_multi(self):
        for w in self.scroll_multi.winfo_children():
            w.destroy()

    def _render_multi(self, data: dict):
        days = data.get("days") or []
        if not days:
            ctk.CTkLabel(self.scroll_multi, text="Sem jogos encontrados.", text_color="#9aa4b2").grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return
        rowi = 0
        for day in days:
            date_key = day.get("date","")
            try:
                head = datetime.strptime(date_key, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                head = date_key
            header = ctk.CTkLabel(self.scroll_multi, text=f"dia {head}:", font=ctk.CTkFont(size=15, weight="bold"))
            header.grid(row=rowi, column=0, sticky="w", padx=10, pady=(10,4))
            rowi += 1
            for item in day.get("items", []):
                try:
                    dbr = datetime.strptime(item.get("date_local",""), "%Y-%m-%d").strftime("%d/%m/%Y")
                except Exception:
                    dbr = item.get("date_local","")
                line = f"{item.get('athlete','')} / {item.get('vs','')} / {item.get('tournament','')} / {item.get('time_local','')} / {_plus4_time_str(item.get('date_local',''), item.get('time_local',''))} {dbr}"
                f = ctk.CTkFrame(self.scroll_multi, fg_color="#171a21", corner_radius=10)
                f.grid(row=rowi, column=0, sticky="ew", padx=10, pady=4)
                f.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(f, text=line, anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=8)
                url = item.get("event_url")
                if url:
                    ctk.CTkButton(f, text="Abrir evento", width=120, command=lambda u=url: webbrowser.open_new_tab(u)).grid(row=0, column=1, padx=8, pady=8)
                rowi += 1

    def on_export_multi(self):
        data = self.last_multi
        if not data or not data.get("days"):
            try:
                data = run_multi(next_per_team= int(self.n_multi.get() or 2), tz= self.tz_multi.get().strip() or "America/Fortaleza")
            except Exception:
                data = None
        if not data or not data.get("days"):
            ctk.CTkLabel(self.scroll_multi, text="Nada para exportar.", text_color="#ef4444").grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return
        path = fd.asksaveasfilename(defaultextension=".txt", initialfile="agenda.txt",
                                    filetypes=[("Texto", "*.txt")], initialdir=BASE_DIR)
        if not path:
            return
        lines = []
        for day in data.get("days"):
            ymd = day.get("date","")
            try:
                br = datetime.strptime(ymd, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                br = ymd
            lines.append(f"dia {br}:")
            for item in day.get("items", []):
                try:
                    dbr = datetime.strptime(item.get("date_local",""), "%Y-%m-%d").strftime("%d/%m/%Y")
                except Exception:
                    dbr = item.get("date_local","")
                lines.append(f"{item.get('athlete','')} / {item.get('vs','')} / {item.get('tournament','')} / {item.get('time_local','')} / {_plus4_time_str(item.get('date_local',''), item.get('time_local',''))} {dbr}")
            lines.append("")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines).strip()+"\n")
            self.status_multi.configure(text=f"Exportado: {path}")
        except Exception as e:
            self.status_multi.configure(text=f"Falha ao exportar: {e}")

    # ------------- event loop -------------
    def _tick(self):
        try:
            kind, data = self.q.get_nowait()
        except queue.Empty:
            self.after(100, self._tick)
            return

        if kind == "ok_single":
            self._render_single(data)
            self._set_loading_single(False, "Concluído")
        elif kind == "err_single":
            self._set_loading_single(False, f"Erro: {data}")
            self._clear_results_single()
            ctk.CTkLabel(self.scroll, text=f"Erro: {data}", text_color="#ef4444").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        elif kind == "ok_multi":
            self.last_multi = data
            self._render_multi(data)
            self._set_loading_multi(False, "Concluído")
        elif kind == "err_multi":
            self._set_loading_multi(False, f"Erro: {data}")
            self._clear_multi()
            ctk.CTkLabel(self.scroll_multi, text=f"Erro: {data}", text_color="#ef4444").grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.after(100, self._tick)

if __name__ == "__main__":
    app = App()
    app.mainloop()
