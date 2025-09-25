import tkinter as tk
from tkinter import colorchooser, messagebox, ttk
from tkcalendar import Calendar
import webbrowser
import random

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class PersonalApp(tk.Tk):
    def __init__(self, username="Utilisateur"):
        super().__init__()

        # Configurable state
        self.username = username
        self.primary_color = "#0b2545"  # dark blue (cases/buttons)
        self.bg_color = "#ffffff"       # white (app background)

        # Window config
        self.title("Application personnelle")
        self.geometry("900x700")
        self.minsize(700, 600)

        # Main container
        self.main_frame = tk.Frame(self, bg=self.bg_color)
        self.main_frame.pack(fill="both", expand=True)

        # Settings button (kept outside main_frame; must update when theme changes)
        self.settings_btn = tk.Button(self, text="⚙",
                                      font=("Helvetica Neue", 14, "bold"),
                                      bg=self.bg_color, bd=0,
                                      command=self.open_settings,
                                      relief="flat", padx=6, pady=4)
        self.settings_btn.place(relx=0.97, rely=0.05, anchor="ne")

        # Data stores
        self.todo_tasks = []          # list of (task_text, status)
        self.agenda_events = {}       # dict: {date: [events]}
        self.web_links = []           # list of (title, url, description)
        self.notes_text = ""         # persistent while app runs

        # Statistics data: list of dicts {"title":..., "value":..., "color":...}
        self.stats = []

        # Build UI
        self.show_home()

    # ----------------- Theme helpers -----------------
    def apply_theme(self):
        # Apply background colors to top-level and main_frame
        try:
            self.configure(bg=self.bg_color)
        except tk.TclError:
            pass
        try:
            self.main_frame.configure(bg=self.bg_color)
        except tk.TclError:
            pass
        try:
            self.settings_btn.configure(bg=self.bg_color)
        except tk.TclError:
            pass

        # Recursively set bg for frames and labels within main_frame.
        # Do NOT change Entries, Buttons, Listboxes, Text, Canvas, etc. to preserve readability.
        def recurse_set_bg(parent):
            for child in parent.winfo_children():
                try:
                    # Frames and LabelFrames -> set background
                    if isinstance(child, (tk.Frame, tk.LabelFrame)):
                        child.configure(bg=self.bg_color)
                    # Labels -> set background (keeps text readable)
                    elif isinstance(child, tk.Label):
                        child.configure(bg=self.bg_color)
                except tk.TclError:
                    pass
                recurse_set_bg(child)

        recurse_set_bg(self.main_frame)

    # ----------------- Core -----------------
    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_main()
        # ensure main_frame background is current
        self.main_frame.configure(bg=self.bg_color)

        # Top: greeting left of todo-list
        top_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        top_frame.pack(fill="x", padx=20, pady=10)

        greeting = tk.Label(top_frame, text=f"Bonjour {self.username}",
                            font=("Helvetica Neue", 20, "bold"),
                            bg=self.bg_color, fg="black")
        greeting.pack(side="left", anchor="n", padx=5)

        # To-do-list (below/next to greeting depending on size)
        todo_frame = tk.LabelFrame(self.main_frame, text="To-do-list",
                                   font=("Helvetica Neue", 16, "bold"),
                                   bg=self.bg_color, fg=self.primary_color,
                                   bd=2, relief="groove", padx=10, pady=10)
        todo_frame.pack(fill="both", padx=20, pady=10, expand=True)

        # container with white background for tasks (keeps contrast)
        self.todo_container = tk.Frame(todo_frame, bg="white")
        self.todo_container.pack(fill="both", expand=True)

        self.render_todo()

        # Modify area (separate, below)
        modify_frame = tk.LabelFrame(self.main_frame, text="Modifier To-do-list",
                                     font=("Helvetica Neue", 14, "bold"),
                                     bg=self.bg_color, fg=self.primary_color,
                                     bd=2, relief="groove", padx=10, pady=10)
        modify_frame.pack(fill="x", padx=20, pady=10)

        self.modify_entry = tk.Entry(modify_frame, font=("Helvetica Neue", 12))
        self.modify_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        save_btn = tk.Button(modify_frame, text="Ajouter",
                             command=self.add_task,
                             bg=self.primary_color, fg="white",
                             font=("Helvetica Neue", 12, "bold"),
                             relief="flat", bd=0, padx=10, pady=5)
        save_btn.pack(side="right", padx=5)

        # Sections grid (uses primary_color)
        sections_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        sections_frame.pack(fill="both", expand=True, padx=20, pady=20)

        sections = [
            ("Agenda", "Agenda"),
            ("Statistiques", "Statistiques"),
            ("Liens web", "Liens"),
            ("Notes rapides", "Notes"),
        ]

        for i, (label, target) in enumerate(sections):
            btn = tk.Button(sections_frame, text=label,
                            command=lambda t=target: self.show_section(t),
                            bg=self.primary_color, fg="white",
                            font=("Helvetica Neue", 14, "bold"),
                            relief="flat", bd=0,
                            padx=20, pady=20)
            btn.grid(row=i // 2, column=i % 2, padx=15, pady=15, sticky="nsew")

        for col in range(2):
            sections_frame.grid_columnconfigure(col, weight=1)
        for row in range(2):
            sections_frame.grid_rowconfigure(row, weight=1)

        # Apply theme to any widgets that were not rebuilt with correct bg
        self.apply_theme()

    # ----------------- To-do -----------------
    def render_todo(self):
        for widget in self.todo_container.winfo_children():
            widget.destroy()

        for idx, (task, status) in enumerate(self.todo_tasks):
            row = tk.Frame(self.todo_container, bg="white")
            row.pack(fill="x", padx=5, pady=2)

            status_label = tk.Label(row, text=status, font=("Helvetica Neue", 14),
                                    bg="white")
            status_label.pack(side="left", padx=5)

            text_label = tk.Label(row, text=task, font=("Helvetica Neue", 14),
                                  bg="white", anchor="w")
            text_label.pack(side="left", fill="x", expand=True, padx=5)

            # validate (green) and refuse (red) indicators implemented with text labels
            check_btn = tk.Button(row, text="Valider",
                                  command=lambda i=idx: self.update_task(i, "✅"),
                                  relief="flat", bg=self.primary_color, fg="white")
            check_btn.pack(side="right", padx=2)

            cross_btn = tk.Button(row, text="Refuser",
                                  command=lambda i=idx: self.update_task(i, "❌"),
                                  relief="flat", bg=self.primary_color, fg="white")
            cross_btn.pack(side="right", padx=2)

            del_btn = tk.Button(row, text="Supprimer",
                                command=lambda i=idx: self.delete_task(i),
                                relief="flat", bg="#e74c3c", fg="white")
            del_btn.pack(side="right", padx=8)

    def add_task(self):
        text = self.modify_entry.get().strip()
        if not text:
            return
        self.todo_tasks.append((text, ""))
        self.modify_entry.delete(0, tk.END)
        self.render_todo()

    def update_task(self, index, status):
        task, _ = self.todo_tasks[index]
        self.todo_tasks[index] = (task, status)
        self.render_todo()

    def delete_task(self, index):
        self.todo_tasks.pop(index)
        self.render_todo()

    # ----------------- Agenda -----------------
    def agenda_add_event(self, date, entry, listbox):
        text = entry.get().strip()
        if not text:
            return
        self.agenda_events.setdefault(date, []).append(text)
        entry.delete(0, tk.END)
        self.agenda_refresh_list(date, listbox)

    def agenda_delete_event(self, date, listbox):
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.agenda_events[date].pop(idx)
        self.agenda_refresh_list(date, listbox)

    def agenda_refresh_list(self, date, listbox):
        listbox.delete(0, tk.END)
        for ev in self.agenda_events.get(date, []):
            listbox.insert(tk.END, ev)

    # ----------------- Liens web -----------------
    def add_link(self, title_entry, url_entry, desc_entry, container):
        title, url, desc = title_entry.get().strip(), url_entry.get().strip(), desc_entry.get().strip()
        if not title or not url:
            return
        self.web_links.append((title, url, desc))
        title_entry.delete(0, tk.END)
        url_entry.delete(0, tk.END)
        desc_entry.delete(0, tk.END)
        self.render_links(container)

    def render_links(self, container):
        for widget in container.winfo_children():
            widget.destroy()

        for title, url, desc in self.web_links:
            row = tk.Frame(container, bg="white", pady=5)
            row.pack(fill="x", padx=5)

            link_btn = tk.Button(row, text=title, fg="blue", cursor="hand2",
                                 font=("Helvetica Neue", 14, "underline"),
                                 relief="flat", bg="white",
                                 command=lambda u=url: webbrowser.open(u))
            link_btn.pack(side="left", padx=5)

            desc_label = tk.Label(row, text=desc, font=("Helvetica Neue", 12),
                                  bg="white", fg="black", anchor="w")
            desc_label.pack(side="left", fill="x", expand=True, padx=10)

    # ----------------- Sections -----------------
    def show_section(self, name):
        self.clear_main()
        self.main_frame.configure(bg=self.bg_color)

        title = tk.Label(self.main_frame, text=name,
                         font=("Helvetica Neue", 22, "bold"),
                         bg=self.bg_color, fg="black")
        title.pack(pady=20)

        content_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        if name == "Agenda":
            cal = Calendar(content_frame, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(pady=10)

            listbox = tk.Listbox(content_frame, font=("Helvetica Neue", 12),
                                 height=8, width=50)
            listbox.pack(pady=10)

            entry = tk.Entry(content_frame, font=("Helvetica Neue", 12))
            entry.pack(pady=5, fill="x")

            add_btn = tk.Button(content_frame, text="Ajouter évènement",
                                command=lambda: self.agenda_add_event(cal.get_date(), entry, listbox),
                                bg=self.primary_color, fg="white")
            add_btn.pack(pady=2)

            del_btn = tk.Button(content_frame, text="Supprimer évènement",
                                command=lambda: self.agenda_delete_event(cal.get_date(), listbox),
                                bg=self.primary_color, fg="white")
            del_btn.pack(pady=2)

            def update_events(event=None):
                self.agenda_refresh_list(cal.get_date(), listbox)
            cal.bind("<<CalendarSelected>>", update_events)

        elif name == "Liens":
            form = tk.Frame(content_frame, bg=self.bg_color)
            form.pack(fill="x", pady=5)

            tk.Label(form, text="Titre:", bg=self.bg_color).grid(row=0, column=0, sticky="w")
            title_entry = tk.Entry(form)
            title_entry.grid(row=0, column=1, sticky="ew", padx=5)

            tk.Label(form, text="URL:", bg=self.bg_color).grid(row=1, column=0, sticky="w")
            url_entry = tk.Entry(form)
            url_entry.grid(row=1, column=1, sticky="ew", padx=5)

            tk.Label(form, text="Description:", bg=self.bg_color).grid(row=2, column=0, sticky="w")
            desc_entry = tk.Entry(form)
            desc_entry.grid(row=2, column=1, sticky="ew", padx=5)

            form.grid_columnconfigure(1, weight=1)

            container = tk.Frame(content_frame, bg="white", bd=1, relief="solid")
            container.pack(fill="both", expand=True, pady=10)

            add_btn = tk.Button(form, text="Ajouter lien",
                                command=lambda: self.add_link(title_entry, url_entry, desc_entry, container),
                                bg=self.primary_color, fg="white")
            add_btn.grid(row=3, column=0, columnspan=2, pady=5)

            self.render_links(container)

        elif name == "Notes":
            txt = tk.Text(content_frame, font=("Helvetica Neue", 14), wrap="word", bg="white")
            txt.insert("1.0", self.notes_text)
            txt.pack(fill="both", expand=True)

            def save_notes(event=None):
                self.notes_text = txt.get("1.0", tk.END).strip()
            txt.bind("<KeyRelease>", save_notes)

        elif name == "Statistiques":
            # Form to add a stat entry
            form = tk.Frame(content_frame, bg=self.bg_color)
            form.pack(fill="x", pady=5)

            tk.Label(form, text="Titre:", bg=self.bg_color).grid(row=0, column=0, sticky="w")
            stat_title = tk.Entry(form)
            stat_title.grid(row=0, column=1, sticky="ew", padx=5)

            tk.Label(form, text="Valeur (€):", bg=self.bg_color).grid(row=1, column=0, sticky="w")
            stat_value = tk.Entry(form)
            stat_value.grid(row=1, column=1, sticky="ew", padx=5)

            # Color chooser for this stat
            chosen_color_var = tk.StringVar(value="#%06x" % random.randint(0, 0xFFFFFF))

            def pick_color():
                c = colorchooser.askcolor(title="Choisir couleur pour cette valeur")[1]
                if c:
                    chosen_color_var.set(c)
                    color_preview.configure(bg=c)

            color_btn = tk.Button(form, text="Choisir couleur",
                                  command=pick_color, bg=self.primary_color, fg="white")
            color_btn.grid(row=0, column=2, rowspan=2, padx=8)

            color_preview = tk.Frame(form, width=36, height=24, bg=chosen_color_var.get(), bd=1, relief="sunken")
            color_preview.grid(row=0, column=3, rowspan=2, padx=5)

            form.grid_columnconfigure(1, weight=1)

            # Treeview to list the stats
            list_frame = tk.Frame(content_frame, bg=self.bg_color)
            list_frame.pack(fill="both", expand=True, pady=10)

            columns = ("titre", "valeur")
            tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
            tree.heading("titre", text="Titre")
            tree.heading("valeur", text="Valeur (€)")
            tree.column("titre", anchor="w")
            tree.column("valeur", anchor="e", width=120)
            tree.pack(side="left", fill="both", expand=True, padx=(0, 5))

            # Small canvas on right for color swatches and actions
            right_panel = tk.Frame(list_frame, bg=self.bg_color)
            right_panel.pack(side="right", fill="y")

            swatches_frame = tk.Frame(right_panel, bg=self.bg_color)
            swatches_frame.pack(fill="y", pady=5)

            # Buttons
            def add_stat():
                title = stat_title.get().strip()
                val_raw = stat_value.get().strip().replace(',', '.')
                if not title or not val_raw:
                    return
                try:
                    val = float(val_raw)
                except ValueError:
                    messagebox.showerror("Erreur", "Valeur non valide. Utilisez un nombre.")
                    return
                color = chosen_color_var.get() or ("#%06x" % random.randint(0, 0xFFFFFF))
                self.stats.append({"title": title, "value": val, "color": color})
                stat_title.delete(0, tk.END)
                stat_value.delete(0, tk.END)
                chosen_color_var.set("#%06x" % random.randint(0, 0xFFFFFF))
                color_preview.configure(bg=chosen_color_var.get())
                self.render_stats(tree, swatches_frame, canvas_container)

            def del_stat():
                sel = tree.selection()
                if not sel:
                    return
                idx = int(sel[0])
                # tree item ids will be string indices we set
                try:
                    self.stats.pop(idx)
                except Exception:
                    pass
                self.render_stats(tree, swatches_frame, canvas_container)

            add_btn = tk.Button(form, text="Ajouter",
                                command=add_stat, bg=self.primary_color, fg="white")
            add_btn.grid(row=2, column=0, columnspan=2, pady=6)

            del_btn = tk.Button(form, text="Supprimer sélection",
                                command=del_stat, bg="#e74c3c", fg="white")
            del_btn.grid(row=2, column=2, columnspan=2, pady=6)

            # Pie chart area
            canvas_container = tk.Frame(content_frame, bg=self.bg_color)
            canvas_container.pack(fill="both", expand=True)

            # Initial render
            self.render_stats(tree, swatches_frame, canvas_container)

        back_btn = tk.Button(self.main_frame, text="Retour",
                             command=lambda: self.show_home(),
                             bg=self.primary_color, fg="white",
                             font=("Helvetica Neue", 12, "bold"),
                             relief="flat", bd=0, padx=15, pady=8)
        back_btn.pack(pady=10)

        # ensure new section widgets get the theme applied
        self.apply_theme()

    # ----------------- Statistiques renderer -----------------
    def render_stats(self, tree, swatches_frame, canvas_container):
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)

        # Fill tree and swatches
        for w in swatches_frame.winfo_children():
            w.destroy()

        total = 0.0
        for i, s in enumerate(self.stats):
            tree.insert("", "end", iid=str(i), values=(s["title"], f"{s["value"]:.2f}"))
            total += s["value"]
            sw = tk.Frame(swatches_frame, bg=self.bg_color)
            sw.pack(fill="x", pady=2)

            color_box = tk.Frame(sw, width=26, height=18, bg=s["color"], bd=1, relief="sunken")
            color_box.pack(side="left", padx=5)

            lbl = tk.Label(sw, text=f"{s['title']} — {s['value']:.2f}€", bg=self.bg_color, anchor="w")
            lbl.pack(side="left", padx=6)

        # Draw pie chart
        for child in canvas_container.winfo_children():
            child.destroy()

        fig = plt.Figure(figsize=(4, 3), dpi=100)
        ax = fig.add_subplot(111)

        if self.stats and total > 0:
            labels = [s["title"] for s in self.stats]
            sizes = [s["value"] for s in self.stats]
            colors = [s["color"] for s in self.stats]
            # autopct show percentage
            ax.pie(sizes, labels=None, colors=colors, startangle=90, wedgeprops={"edgecolor": "w"})
            ax.axis('equal')
            # legend with values
            ax.legend([f"{l}: {v:.2f}€" for l, v in zip(labels, sizes)], loc='center left', bbox_to_anchor=(1, 0.5))
            ax.set_title(f"Total: {total:.2f}€")
        else:
            ax.text(0.5, 0.5, 'Aucune donnée', horizontalalignment='center', verticalalignment='center')
            ax.axis('off')

        canvas = FigureCanvasTkAgg(fig, master=canvas_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ----------------- Settings -----------------
    def open_settings(self):
        self.clear_main()
        self.main_frame.configure(bg=self.bg_color)

        tk.Label(self.main_frame, text="Paramètres",
                 font=("Helvetica Neue", 22, "bold"),
                 bg=self.bg_color, fg="black").pack(pady=20)

        # Username change
        tk.Label(self.main_frame, text="Nom d'utilisateur:",
                 font=("Helvetica Neue", 14), bg=self.bg_color).pack(pady=5)
        name_entry = tk.Entry(self.main_frame, font=("Helvetica Neue", 14))
        name_entry.insert(0, self.username)
        name_entry.pack(pady=5)

        def save_name():
            self.username = name_entry.get().strip() or "Utilisateur"
            self.show_home()

        save_name_btn = tk.Button(self.main_frame, text="Changer le nom",
                                  command=save_name,
                                  bg=self.primary_color, fg="white",
                                  font=("Helvetica Neue", 12, "bold"))
        save_name_btn.pack(pady=10)

        # Background color (apply immediately to whole app)
        def change_bg():
            color = colorchooser.askcolor(title="Choisir couleur de fond")[1]
            if color:
                self.bg_color = color
                # Apply theme without leaving settings view
                self.apply_theme()

        bg_btn = tk.Button(self.main_frame, text="Changer couleur fond",
                           command=change_bg,
                           bg=self.primary_color, fg="white",
                           font=("Helvetica Neue", 12, "bold"))
        bg_btn.pack(pady=5)

        # Primary color (rebuild UI so buttons use new color)
        def change_primary():
            color = colorchooser.askcolor(title="Choisir couleur des cases")[1]
            if color:
                self.primary_color = color
                # Recreate current view so newly created buttons use the new primary color.
                # If user is in settings, we re-open settings so they remain here but with updated colors.
                self.show_home()
                self.open_settings()

        primary_btn = tk.Button(self.main_frame, text="Changer couleur cases",
                                command=change_primary,
                                bg=self.primary_color, fg="white",
                                font=("Helvetica Neue", 12, "bold"))
        primary_btn.pack(pady=5)

        back_btn = tk.Button(self.main_frame, text="Retour",
                             command=lambda: self.show_home(),
                             bg=self.primary_color, fg="white",
                             font=("Helvetica Neue", 12, "bold"),
                             relief="flat", bd=0, padx=15, pady=8)
        back_btn.pack(pady=20)

        # Make sure the settings button itself matches the new theme immediately
        self.apply_theme()


if __name__ == "__main__":
    app = PersonalApp(username="Théo")
    app.mainloop()
