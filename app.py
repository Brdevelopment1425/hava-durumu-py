import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from PIL import Image, ImageTk
from io import BytesIO

API_KEY = ""

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hava Durumu ")
        self.geometry("800x650")
        self.configure(bg="#121212")

        self.city_var = tk.StringVar()
        self.suggestions = []  # API'den gelen şehir önerileri (dict listesi)
        self.history = []

        self.create_widgets()

    def create_widgets(self):
        # --- Arama çubuğu ---
        search_frame = tk.Frame(self, bg="#1f1f1f", pady=15, padx=15)
        search_frame.pack(fill="x", padx=20, pady=(20, 5))

        lbl = tk.Label(search_frame, text="Şehir Adı:", fg="#eeeeee", bg="#1f1f1f", font=("Segoe UI", 14, "bold"))
        lbl.pack(side="left")

        city_entry = tk.Entry(search_frame, textvariable=self.city_var, font=("Segoe UI", 14), width=30,
                              bg="#2a2a2a", fg="#eeeeee", insertbackground="white", relief="flat")
        city_entry.pack(side="left", padx=10)
        city_entry.bind("<KeyRelease>", self.on_keyrelease)
        city_entry.bind("<Return>", lambda e: self.on_search_confirm())

        search_btn = tk.Button(search_frame, text="Getir", command=self.on_search_confirm, font=("Segoe UI", 14),
                               bg="#00bcd4", fg="#121212", relief="flat", padx=10, pady=5, activebackground="#0097a7")
        search_btn.pack(side="left")

        # --- Öneri listesi ---
        self.suggestion_box = tk.Listbox(self, height=5, bg="#1f1f1f", fg="#eeeeee", font=("Segoe UI", 12),
                                         selectbackground="#00bcd4", selectforeground="#121212", relief="flat")
        self.suggestion_box.pack(fill="x", padx=20, pady=(0, 10))
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_suggestion_select)
        self.suggestion_box.pack_forget()  # Başta gizli

        # --- Arama geçmişi ---
        self.history_listbox = tk.Listbox(self, height=5, bg="#1f1f1f", fg="#eeeeee", font=("Segoe UI", 12),
                                          selectbackground="#00bcd4", selectforeground="#121212", relief="flat")
        self.history_listbox.pack(fill="x", padx=20, pady=(0, 10))
        self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)

        # --- Hava Durumu Kartı ---
        self.weather_card = tk.Frame(self, bg="#1e1e1e", bd=2, relief="ridge", padx=20, pady=20)
        self.weather_card.pack(padx=20, pady=10, fill="both", expand=True)

        self.left_frame = tk.Frame(self.weather_card, bg="#1e1e1e")
        self.left_frame.pack(side="left", fill="y", padx=(0, 30))

        self.weather_icon_label = tk.Label(self.left_frame, bg="#1e1e1e")
        self.weather_icon_label.pack(pady=10)

        self.city_label = tk.Label(self.left_frame, text="", font=("Segoe UI", 24, "bold"), fg="#00bcd4", bg="#1e1e1e")
        self.city_label.pack(pady=(10,5))

        self.desc_label = tk.Label(self.left_frame, text="", font=("Segoe UI", 16), fg="#eeeeee", bg="#1e1e1e")
        self.desc_label.pack(pady=(0,10))

        self.temp_label = tk.Label(self.left_frame, text="", font=("Segoe UI", 48, "bold"), fg="#ffffff", bg="#1e1e1e")
        self.temp_label.pack(pady=(5, 20))

        self.right_frame = tk.Frame(self.weather_card, bg="#1e1e1e")
        self.right_frame.pack(side="left", fill="both", expand=True)

        details_font = ("Segoe UI", 14)
        label_fg = "#bbbbbb"
        value_fg = "#ffffff"

        self.details = {}
        detail_keys = [
            ("Hissedilen Sıcaklık", "feels_like"),
            ("Nem", "humidity"),
            ("Basınç", "pressure"),
            ("Rüzgar Hızı", "wind_speed"),
            ("Gün Doğumu", "sunrise"),
            ("Gün Batımı", "sunset"),
        ]

        for text, key in detail_keys:
            frame = tk.Frame(self.right_frame, bg="#1e1e1e")
            frame.pack(anchor="w", pady=8, fill="x")

            lbl_text = tk.Label(frame, text=text+":", font=details_font, fg=label_fg, bg="#1e1e1e")
            lbl_text.pack(side="left")

            lbl_value = tk.Label(frame, text="", font=details_font, fg=value_fg, bg="#1e1e1e", anchor="w")
            lbl_value.pack(side="left", padx=(10,0))

            self.details[key] = lbl_value

    def on_keyrelease(self, event):
        # Kullanıcı yazdıkça şehir önerisi çek ve listele
        query = self.city_var.get().strip()
        if len(query) < 2:
            self.suggestion_box.pack_forget()
            return
        try:
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=5&appid={API_KEY}"
            response = requests.get(url)
            data = response.json()
            if not data:
                self.suggestion_box.pack_forget()
                self.suggestions = []
                return

            self.suggestions = data
            self.suggestion_box.delete(0, tk.END)
            for city in data:
                name = city.get("name", "")
                state = city.get("state", "")
                country = city.get("country", "")
                display_name = f"{name}, {state + ', ' if state else ''}{country}"
                self.suggestion_box.insert(tk.END, display_name)
            self.suggestion_box.pack(fill="x", padx=20, pady=(0,10))
        except:
            self.suggestion_box.pack_forget()
            self.suggestions = []

    def on_suggestion_select(self, event):
        if not self.suggestion_box.curselection():
            return
        index = self.suggestion_box.curselection()[0]
        selected_city = self.suggestions[index]
        city_display_name = self.suggestion_box.get(index)
        self.city_var.set(city_display_name.split(",")[0])
        self.suggestion_box.pack_forget()
        self.get_weather_by_coords(selected_city['lat'], selected_city['lon'], city_display_name)

    def on_search_confirm(self):
        query = self.city_var.get().strip()
        if not query:
            messagebox.showwarning("Uyarı", "Lütfen bir şehir adı girin.")
            return

        # Arama yapılmadan önce eşleşme kontrolü
        try:
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={API_KEY}"
            response = requests.get(url)
            data = response.json()
            if not data:
                messagebox.showerror("Hata", f"'{query}' için yakın eşleşme bulunamadı.")
                return

            city_info = data[0]
            city_display_name = f"{city_info['name']}, {city_info.get('state','') + ', ' if city_info.get('state') else ''}{city_info['country']}"

            self.city_var.set(city_info['name'])
            self.suggestion_box.pack_forget()
            self.get_weather_by_coords(city_info['lat'], city_info['lon'], city_display_name)

        except Exception as e:
            messagebox.showerror("Hata", f"Bir hata oluştu: {e}")

    def get_weather_by_coords(self, lat, lon, city_display_name):
        try:
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=tr"
            weather_resp = requests.get(weather_url)
            weather_data = weather_resp.json()

            desc = weather_data['weather'][0]['description'].capitalize()
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            humidity = weather_data['main']['humidity']
            pressure = weather_data['main']['pressure']
            wind_speed = weather_data['wind']['speed']

            sunrise_ts = weather_data['sys']['sunrise']
            sunset_ts = weather_data['sys']['sunset']
            sunrise = datetime.fromtimestamp(sunrise_ts).strftime('%H:%M')
            sunset = datetime.fromtimestamp(sunset_ts).strftime('%H:%M')

            icon_code = weather_data['weather'][0]['icon']
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
            icon_resp = requests.get(icon_url)
            icon_img = Image.open(BytesIO(icon_resp.content))
            icon_photo = ImageTk.PhotoImage(icon_img)

            # Güncelle
            self.weather_icon_label.config(image=icon_photo)
            self.weather_icon_label.image = icon_photo

            self.city_label.config(text=city_display_name)
            self.desc_label.config(text=desc)
            self.temp_label.config(text=f"{temp:.1f}°C")

            self.details["feels_like"].config(text=f"{feels_like:.1f}°C")
            self.details["humidity"].config(text=f"%{humidity}")
            self.details["pressure"].config(text=f"{pressure} hPa")
            self.details["wind_speed"].config(text=f"{wind_speed} m/s")
            self.details["sunrise"].config(text=sunrise)
            self.details["sunset"].config(text=sunset)

            self.add_to_history(city_display_name)

        except Exception as e:
            messagebox.showerror("Hata", f"Bir hata oluştu: {e}")

    def add_to_history(self, city_display_name):
        if city_display_name not in self.history:
            self.history.append(city_display_name)
            self.history_listbox.insert(tk.END, city_display_name)

    def on_history_select(self, event):
        if not self.history_listbox.curselection():
            return
        index = self.history_listbox.curselection()[0]
        city_display_name = self.history[index]

        # Şehir ve ülke bilgisi stringden ayrılır (ör: İstanbul, İstanbul, TR)
        parts = city_display_name.split(",")
        city = parts[0].strip()

        # Yeniden api ile koordinat bulup güncelle
        try:
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
            response = requests.get(url)
            data = response.json()
            if not data:
                messagebox.showerror("Hata", "Şehir bulunamadı.")
                return
            city_info = data[0]
            self.get_weather_by_coords(city_info['lat'], city_info['lon'], city_display_name)
        except Exception as e:
            messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
