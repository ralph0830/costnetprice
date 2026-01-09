import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import datetime
import os
import sqlite3 
import openpyxl # For Excel Export
from shutil import copyfile # For copying template file
import sys # For PyInstaller path detection

YARN_DB_JSON_FILE = "yarn_db.json"
HISTORY_DB_FILE = "calculation_history.db"
EXCEL_TEMPLATE_FILE = "FabricCost_Form.xlsx" # Excel 템플릿 파일명

# --- General Utils ---
def get_current_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- JSON DB Utils ---
def load_yarns_from_json():
    if not os.path.exists(YARN_DB_JSON_FILE):
        print(f"{YARN_DB_JSON_FILE} does not exist. Returning empty list.")
        return [] 
    
    file_content = None
    try:
        if os.path.getsize(YARN_DB_JSON_FILE) == 0:
            print(f"Warning: {YARN_DB_JSON_FILE} is empty. Returning empty list.")
            return []
            
        with open(YARN_DB_JSON_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read() 
            
        if not file_content or not file_content.strip(): 
            print(f"Warning: {YARN_DB_JSON_FILE} is empty or contains only whitespace after reading. Returning empty list.")
            return []
            
        data = json.loads(file_content) 
        return data if isinstance(data, list) else [] 
            
    except json.JSONDecodeError as e:
        content_preview = file_content[:100] if file_content else "N/A"
        print(f"JSON Decode Error in {YARN_DB_JSON_FILE}: {e}. Content preview: '{content_preview}...' Returning empty list.")
        return []
    except OSError as e:
        print(f"OSError while processing {YARN_DB_JSON_FILE}: {e}.")
        print(f"Absolute path attempted: {os.path.abspath(YARN_DB_JSON_FILE)}")
        print(f"Current working directory: {os.getcwd()}")
        print("Returning empty list due to OSError.")
        return []
    except Exception as e: 
        print(f"Unexpected error processing {YARN_DB_JSON_FILE}: {e}. Returning empty list.")
        return []


def save_yarns_to_json(yarn_list):
    try:
        with open(YARN_DB_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(yarn_list, f, ensure_ascii=False, indent=4)
    except IOError as e: messagebox.showerror("JSON 저장 오류", f"원사 DB 파일 저장에 실패했습니다:\n{e}")

def generate_yarn_display_description(yarn_details_dict):
    try:
        desc = f"{yarn_details_dict.get('yarn_type','N/A')}({yarn_details_dict.get('recycle_status','N/A')}) "
        denier_val = yarn_details_dict.get('denier',0)
        filament_val = yarn_details_dict.get('filament',0)
        if denier_val or filament_val: 
            desc += f"{int(denier_val) if denier_val else ''}D/" \
                    f"{int(filament_val) if filament_val else ''}F "
        desc += f"{yarn_details_dict.get('processing_type','N/A')} {yarn_details_dict.get('luster','N/A')}"
        desc = desc.replace("0D/0F ", "").replace(" D/ F","").replace("N/A(N/A) ","").replace("N/A N/A","").strip()
        quality = yarn_details_dict.get('quality', '일반')
        desc += f" ({quality})"
        return desc.strip()
    except Exception: return "정보 조합 오류"

def ensure_default_yarns_in_json():
    yarns = load_yarns_from_json()
    if not yarns:
        PREDEFINED_YARNS_FOR_JSON_INIT = [
            {"id": 1, "yarn_type": "Polyester", "denier": 150, "filament": 72, "processing_type": "DTY", "luster": "SD", "recycle_status": "virgin", "price_value": 0.80, "price_currency": "$", "price_unit": "lb", "quality": "일반", "created_at": get_current_timestamp(), "updated_at": get_current_timestamp()},
            {"id": 2, "yarn_type": "Polyester", "denier": 75, "filament": 36, "processing_type": "DTY", "luster": "BRT", "recycle_status": "recycled", "price_value": 1.20, "price_currency": "$", "price_unit": "lb", "quality": "AAA", "created_at": get_current_timestamp(), "updated_at": get_current_timestamp()},
            {"id": 3, "yarn_type": "Nylon", "denier": 70, "filament": 68, "processing_type": "ATY", "luster": "SD", "recycle_status": "virgin", "price_value": 2500, "price_currency": "원화", "price_unit": "kg", "quality": "일반", "created_at": get_current_timestamp(), "updated_at": get_current_timestamp()},
            {"id": 4, "yarn_type": "Custom", "denier": 0, "filament": 0, "processing_type": "N/A", "luster": "N/A", "recycle_status": "N/A", "price_value": 0.80, "price_currency": "$", "price_unit": "lb", "quality": "일반", "created_at": get_current_timestamp(), "updated_at": get_current_timestamp()}
        ]
        save_yarns_to_json(PREDEFINED_YARNS_FOR_JSON_INIT)
        print(f"Initialized {YARN_DB_JSON_FILE} with default data.")

# --- History DB Utils ---
def init_history_db():
    conn = sqlite3.connect(HISTORY_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calculation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calculation_date TEXT NOT NULL,
            item_name TEXT,
            inputs_json TEXT,
            base_rate_results_json TEXT 
        )
    """)
    conn.commit()
    conn.close()

def save_calculation_to_history(item_name, inputs_dict, base_rate_results_dict):
    conn = sqlite3.connect(HISTORY_DB_FILE)
    cursor = conn.cursor()
    calc_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inputs_str = json.dumps(inputs_dict, ensure_ascii=False)
    results_str = json.dumps(base_rate_results_dict, ensure_ascii=False)
    try:
        cursor.execute("""
            INSERT INTO calculation_history (calculation_date, item_name, inputs_json, base_rate_results_json)
            VALUES (?, ?, ?, ?)
        """, (calc_date, item_name, inputs_str, results_str))
        conn.commit()
    except Exception as e:
        messagebox.showerror("History 저장 오류", f"계산 내역 저장 중 오류 발생:\n{e}")
    finally:
        conn.close()

def load_history_summary():
    conn = sqlite3.connect(HISTORY_DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, calculation_date, item_name FROM calculation_history ORDER BY calculation_date DESC")
        return cursor.fetchall()
    except Exception as e:
        messagebox.showerror("History 로드 오류", f"계산 내역 로드 중 오류 발생:\n{e}")
        return []
    finally:
        conn.close()

def load_history_detail(history_id):
    conn = sqlite3.connect(HISTORY_DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT inputs_json, base_rate_results_json FROM calculation_history WHERE id = ?", (history_id,))
        row = cursor.fetchone()
        if row:
            inputs = json.loads(row[0])
            results = json.loads(row[1]) 
            return inputs, results
        return None, None
    except Exception as e:
        messagebox.showerror("History 상세 로드 오류", f"계산 상세 내역 로드 중 오류 발생:\n{e}")
        return None, None
    finally:
        conn.close()


class YarnManagementWindow(tk.Toplevel):
    def __init__(self, parent, refresh_callback):
        super().__init__(parent)
        self.title("원사 DB 관리 (JSON)")
        self.geometry("950x700") 
        self.transient(parent)
        self.grab_set()
        self.refresh_callback = refresh_callback
        self.all_yarns_data = load_yarns_from_json() 

        self.style = ttk.Style(self)
        self.style.theme_use('clam') 
        self.style.configure("Blue.TFrame", background="#E1F5FE") 
        self.style.configure("Blue.TLabel", background="#E1F5FE", foreground="#01579B") 
        self.style.configure("Blue.TButton", background="#03A9F4", foreground="white", borderwidth=1) 
        self.style.map("Blue.TButton", background=[('active', '#0288D1')])
        self.style.configure("Blue.TLabelframe", background="#E1F5FE", bordercolor="#0277BD", relief="groove")
        self.style.configure("Blue.TLabelframe.Label", background="#90CAF9", foreground="#01579B", padding=3, font=('Helvetica', 9, 'bold'))
        self.style.configure("Blue.Treeview.Heading", background="#B3E5FC", foreground="#01579B", font=('Helvetica', 10, 'bold'))
        self.style.configure("Blue.TRadiobutton", background="#E1F5FE", foreground="#01579B")
        self.style.map('Blue.TCombobox', selectbackground=[('readonly', 'blue')], selectforeground=[('readonly', 'white')])


        main_db_frame = ttk.Frame(self, style="Blue.TFrame")
        main_db_frame.pack(fill=tk.BOTH, expand=True)


        self.yarn_fields_config_for_form = { 
            "yarn_type": {"label": "사종", "type": tk.StringVar, "options": ["Polyester", "Spandex", "Nylon", "Cotton", "Rayon", "Tencel", "Modal", "Acetate", "Linen", "Wool"], "width": 15, "default": "Polyester"},
            "denier": {"label": "Denier(D)", "type": tk.DoubleVar, "width": 7, "numeric": True, "default": 0.0},
            "filament": {"label": "Filament(F)", "type": tk.DoubleVar, "width": 7, "numeric": True, "default": 0.0},
            "processing_type": {"label": "사가공", "type": tk.StringVar, "options": ["DTY", "FY", "ATY", "ITY", "Spun", "FDY", "POY"], "width": 10, "default": "DTY"},
            "luster": {"label": "광택", "type": tk.StringVar, "options": ["SD", "BRT", "FD", "CDP", "Matte"], "width": 10, "default": "SD"},
            "recycle_status": {"label": "Recycle 여부", "type": tk.StringVar, "options": ["virgin", "recycled"], "control": "radio", "default": "virgin"},
            "quality": {"label": "품질", "type": tk.StringVar, "options": ["일반", "AAA"], "control": "radio", "default": "일반"}, 
            "price_currency": {"label": "단가 통화", "type": tk.StringVar, "options": ["$", "원화"], "control": "radio", "default": "$"},
            "price_unit": {"label": "단가 단위", "type": tk.StringVar, "options": ["lb", "kg"], "control": "radio", "default": "lb"},
            "price_value": {"label": "단가 금액", "type": tk.DoubleVar, "width": 10, "numeric": True, "default": 0.0},
        }
        self.entry_vars = {}
        self.current_selected_yarn_id_in_editor = None 
        self.current_sort_column = "display_description" 
        self.current_sort_ascending = True

        self._setup_ui(main_db_frame) 
        self.load_yarns_to_tree()

    def _setup_ui(self, parent_frame): 
        tree_frame = ttk.Frame(parent_frame, style="Blue.TFrame")
        tree_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.tree_display_columns_info = {
            "id": {"label": "ID", "width": 40, "numeric": True, "visible": True}, 
            "display_description": {"label": "원사명(표시용)", "width": 450, "numeric": False, "visible": True}, 
            "price_value": {"label": "단가 금액", "width": 100, "numeric": True, "visible": True}, 
            "combined_unit": {"label": "단위", "width": 100, "numeric": False, "visible": True}, 
            "updated_at": {"label": "최종수정일", "width": 150, "numeric": False, "visible": True}, 
            "yarn_type": {"label": "사종", "visible": False, "numeric": False},
            "denier": {"label": "Denier", "visible": False, "numeric": True},"filament": {"label": "Filament", "visible": False, "numeric": True},"processing_type": {"label": "사가공", "visible": False, "numeric": False},"luster": {"label": "광택", "visible": False, "numeric": False},"recycle_status": {"label": "Recycle", "visible": False, "numeric": False},"quality": {"label": "품질", "visible": False, "numeric": False},"price_currency": {"label": "통화", "visible": False, "numeric": False},"price_unit": {"label": "단위(원본)", "visible": False, "numeric": False}
        }
        
        visible_tree_cols = [col_id for col_id, info in self.tree_display_columns_info.items() if info["visible"]]
        self.tree = ttk.Treeview(tree_frame, columns=visible_tree_cols, show='headings', style="Blue.Treeview") 
        
        for col_id in visible_tree_cols:
            info = self.tree_display_columns_info[col_id]
            self.tree.heading(col_id, text=info["label"], 
                              command=lambda c=col_id, n=info["numeric"]: self._sort_tree_column_click(c, n))
            self.tree.column(col_id, width=info["width"], anchor=tk.W, stretch=tk.YES if col_id == "display_description" else tk.NO)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_yarn_select_in_editor)

        form_frame = ttk.LabelFrame(parent_frame, text="원사 정보 입력/수정", style="Blue.TLabelframe")
        form_frame.pack(pady=10, padx=10, fill=tk.X)
        grid_row = 0
        for key, config in self.yarn_fields_config_for_form.items(): 
            field_label = ttk.Label(form_frame, text=config['label'] + ":", style="Blue.TLabel")
            field_label.grid(row=grid_row, column=0, sticky=tk.W, padx=5, pady=3)
            var = config['type']()
            self.entry_vars[key] = var
            entry_width = config.get('width', 15)
            if config.get("control") == "radio":
                radio_frame = ttk.Frame(form_frame, style="Blue.TFrame")
                radio_frame.grid(row=grid_row, column=1, sticky=tk.W, padx=5, pady=0, columnspan=3) 
                for i, option_val in enumerate(config["options"]):
                    rb = ttk.Radiobutton(radio_frame, text=option_val, variable=var, value=option_val, style="Blue.TRadiobutton") 
                    rb.pack(side=tk.LEFT, padx=(0, 10))
                if config["options"]: var.set(config["options"][0]) 
            elif "options" in config: 
                entry = ttk.Combobox(form_frame, textvariable=var, values=config["options"], width=entry_width -2, state="readonly", style="Blue.TCombobox") 
                if config["options"]: var.set(config["options"][0])
                entry.grid(row=grid_row, column=1, sticky=tk.EW, padx=5, pady=3)
            else: 
                entry = ttk.Entry(form_frame, textvariable=var, width=entry_width) 
                entry.grid(row=grid_row, column=1, sticky=tk.EW, padx=5, pady=3)
            grid_row += 1
        form_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(parent_frame, style="Blue.TFrame")
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="신규 저장", command=self.add_yarn, style="Blue.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="수정 저장", command=self.update_yarn, style="Blue.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="삭제", command=self.delete_yarn, style="Blue.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="필드 초기화", command=self.clear_fields, style="Blue.TButton").pack(side=tk.LEFT, padx=5)

    def _sort_tree_column_click(self, col_id, is_numeric):
        if self.current_sort_column == col_id:
            self.current_sort_ascending = not self.current_sort_ascending
        else:
            self.current_sort_column = col_id
            self.current_sort_ascending = True
        self.load_yarns_to_tree(sort_by_column=col_id, sort_ascending=self.current_sort_ascending, is_numeric_col_flag=is_numeric)

    def load_yarns_to_tree(self, sort_by_column=None, sort_ascending=True, is_numeric_col_flag=False):
        if sort_by_column is None:
            sort_by_column = self.current_sort_column
            sort_ascending = self.current_sort_ascending
            is_numeric_col_flag = self.tree_display_columns_info.get(sort_by_column,{}).get('numeric', False)
            
        for i in self.tree.get_children(): self.tree.delete(i)
        
        processed_yarns_for_display = []
        for yarn_dict_from_json in self.all_yarns_data:
            display_desc = generate_yarn_display_description(yarn_dict_from_json)
            combined_unit_display = f"{yarn_dict_from_json.get('price_currency', '')}/{yarn_dict_from_json.get('price_unit', '')}"
            tree_view_values = []
            for col_id_visible in self.tree.cget("columns"): 
                if col_id_visible == "id": tree_view_values.append(yarn_dict_from_json.get('id', ''))
                elif col_id_visible == "display_description": tree_view_values.append(display_desc)
                elif col_id_visible == "combined_unit": tree_view_values.append(combined_unit_display)
                elif col_id_visible == "updated_at": tree_view_values.append(yarn_dict_from_json.get('updated_at', ''))
                elif col_id_visible == "price_value": tree_view_values.append(yarn_dict_from_json.get('price_value', ''))
            sort_value_for_this_row = "" 
            current_col_info_for_sort = self.tree_display_columns_info.get(sort_by_column, {})
            is_current_sort_col_numeric = current_col_info_for_sort.get('numeric', False)
            if sort_by_column == "display_description": sort_value_for_this_row = display_desc.lower()
            elif sort_by_column == "combined_unit": sort_value_for_this_row = combined_unit_display.lower()
            elif sort_by_column in yarn_dict_from_json: 
                sort_value_for_this_row = yarn_dict_from_json[sort_by_column]
                if is_current_sort_col_numeric: 
                    try: sort_value_for_this_row = float(sort_value_for_this_row)
                    except (ValueError, TypeError): sort_value_for_this_row = 0 
                else: sort_value_for_this_row = str(sort_value_for_this_row).lower()
            processed_yarns_for_display.append({"iid": yarn_dict_from_json['id'],"values": tuple(tree_view_values),"sort_value": sort_value_for_this_row})
        processed_yarns_for_display.sort(key=lambda x: x["sort_value"], reverse=not sort_ascending)
        for yarn_item in processed_yarns_for_display:
            self.tree.insert('', tk.END, iid=yarn_item["iid"], values=yarn_item["values"])

    def on_yarn_select_in_editor(self, event=None):
        selected_item_iid_str = self.tree.focus()
        if not selected_item_iid_str: return
        try: selected_item_iid = int(selected_item_iid_str) 
        except ValueError: return 
        selected_yarn_data = next((yarn for yarn in self.all_yarns_data if yarn.get('id') == selected_item_iid), None)
        if selected_yarn_data:
            self.current_selected_yarn_id_in_editor = selected_item_iid
            for key, config in self.yarn_fields_config_for_form.items():
                self.entry_vars[key].set(selected_yarn_data.get(key, config['type']().get())) 
        else: self.clear_fields()

    def clear_fields(self):
        for key, var in self.entry_vars.items():
            config = self.yarn_fields_config_for_form[key]
            default_value = config.get("default")
            if default_value is not None:
                var.set(default_value)
            elif isinstance(var, tk.StringVar): 
                var.set("")
            elif isinstance(var, tk.DoubleVar): 
                var.set(0.0)
        self.current_selected_yarn_id_in_editor = None
        if self.tree.selection(): self.tree.selection_remove(self.tree.selection()[0])

    def _get_form_data(self): 
        data = {}
        current_processing_key = None
        try:
            for key, var in self.entry_vars.items():
                current_processing_key = key
                val = var.get()
                if self.yarn_fields_config_for_form[key]['type'] == tk.DoubleVar:
                    val_str = str(val).strip()
                    if not val_str: val = 0.0 
                    else: val = float(val_str) 
                data[key] = val
            # price_value는 DoubleVar이므로, 비어있거나 유효하지 않으면 0.0을 반환하거나 TclError/ValueError가 발생합니다.
            # 0.0이 유효하지 않은 가격이라면, > 0 보다 큰지 확인하는 것이 더 적절할 수 있습니다.
            # 현재 로직은 price_value가 None인지 확인하는데, DoubleVar는 보통 None을 반환하지 않습니다.
            # 만약 price_value가 0.0인 것을 허용하지 않으려면, data.get('price_value', 0.0) <= 0.0 와 같이 확인해야 합니다.
            # 지금은 기존 메시지를 유지하되, DoubleVar의 특성을 고려하여 주석을 남깁니다.
            if data.get('price_value', 0.0) == 0.0 and self.yarn_fields_config_for_form['price_value']['default'] != 0.0 : # 예시: 기본값이 0이 아닌데 0으로 입력된 경우
                 messagebox.showerror("입력 오류", "단가 금액은 필수 항목입니다.", parent=self)
                 return None
            return data
        except ValueError as e:
            field_label = self.yarn_fields_config_for_form[current_processing_key]['label']
            messagebox.showerror("입력 오류", f"'{field_label}' 항목에 유효한 숫자를 입력해주세요: {e}", parent=self)
            return None
        except tk.TclError as e:
            field_label = self.yarn_fields_config_for_form[current_processing_key]['label']
            messagebox.showerror("입력 오류", f"'{field_label}' 항목의 값을 확인해주세요: {e}", parent=self)
            return None

    def _get_next_id(self):
        if not self.all_yarns_data: return 1
        return max(yarn.get('id', 0) for yarn in self.all_yarns_data) + 1

    def add_yarn(self):
        data = self._get_form_data()
        if not data: return
        ts = get_current_timestamp()
        new_id = self._get_next_id()
        new_yarn_entry = {"id": new_id, **data, "created_at": ts, "updated_at": ts}
        self.all_yarns_data.append(new_yarn_entry)
        try:
            save_yarns_to_json(self.all_yarns_data)
            self.load_yarns_to_tree(sort_by_column=self.current_sort_column, sort_ascending=self.current_sort_ascending)
            self.clear_fields()
            self.refresh_callback() 
            messagebox.showinfo("성공", "원사가 성공적으로 추가되었습니다.", parent=self)
        except Exception as e:
            self.all_yarns_data = [y for y in self.all_yarns_data if y.get('id') != new_id]
            messagebox.showerror("오류", f"원사 추가 실패: {e}", parent=self)

    def update_yarn(self):
        if not self.current_selected_yarn_id_in_editor:
            messagebox.showwarning("선택 필요", "수정할 원사를 목록에서 선택해주세요.", parent=self)
            return
        data_from_form = self._get_form_data()
        if not data_from_form: return
        ts = get_current_timestamp()
        updated_yarn_list = []
        found = False
        for yarn in self.all_yarns_data:
            if yarn.get('id') == self.current_selected_yarn_id_in_editor:
                yarn.update(data_from_form) 
                yarn['updated_at'] = ts    
                found = True
            updated_yarn_list.append(yarn)
        if found:
            self.all_yarns_data = updated_yarn_list
            try:
                save_yarns_to_json(self.all_yarns_data)
                self.load_yarns_to_tree(sort_by_column=self.current_sort_column, sort_ascending=self.current_sort_ascending)
                self.refresh_callback()
                messagebox.showinfo("성공", "원사가 성공적으로 수정되었습니다.", parent=self)
            except Exception as e:
                messagebox.showerror("오류", f"원사 수정 저장 실패: {e}", parent=self)
        else: messagebox.showerror("오류", "선택된 원사를 찾을 수 없습니다.", parent=self)

    def delete_yarn(self):
        if not self.current_selected_yarn_id_in_editor:
            messagebox.showwarning("선택 필요", "삭제할 원사를 목록에서 선택해주세요.", parent=self)
            return
        if messagebox.askyesno("삭제 확인", "정말로 이 원사를 삭제하시겠습니까?", parent=self):
            original_data = list(self.all_yarns_data) 
            self.all_yarns_data = [yarn for yarn in self.all_yarns_data if yarn.get('id') != self.current_selected_yarn_id_in_editor]
            try:
                save_yarns_to_json(self.all_yarns_data)
                self.load_yarns_to_tree(sort_by_column=self.current_sort_column, sort_ascending=self.current_sort_ascending)
                self.clear_fields()
                self.refresh_callback()
                messagebox.showinfo("성공", "원사가 삭제되었습니다.", parent=self)
            except Exception as e:
                self.all_yarns_data = original_data 
                messagebox.showerror("오류", f"원사 삭제 실패: {e}", parent=self)


class HistoryWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("원가 계산 History")
        self.geometry("1000x700")
        self.transient(parent)
        self.grab_set()

        self.style = ttk.Style(self)
        self.style.theme_use('clam') 
        self.style.configure("History.TFrame", background="#F0F4F8")
        self.style.configure("History.TLabel", background="#F0F4F8", foreground="#37474F")
        self.style.configure("History.Treeview.Heading", background="#CFD8DC", foreground="#37474F", font=('Helvetica', 10, 'bold'))
        self.style.configure("History.TLabelframe", background="#F0F4F8", bordercolor="#546E7A")
        self.style.configure("History.TLabelframe.Label", background="#B0BEC5", foreground="#263238", padding=3)


        main_frame = ttk.Frame(self, style="History.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        list_frame = ttk.LabelFrame(main_frame, text="계산 내역", style="History.TLabelframe")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))

        columns = ("id", "date", "item_name")
        self.history_tree = ttk.Treeview(list_frame, columns=columns, show="headings", style="History.Treeview")
        self.history_tree.heading("id", text="ID")
        self.history_tree.column("id", width=50, anchor=tk.W, stretch=tk.NO)
        self.history_tree.heading("date", text="계산일시")
        self.history_tree.column("date", width=150, anchor=tk.W)
        self.history_tree.heading("item_name", text="아이템명")
        self.history_tree.column("item_name", width=200, anchor=tk.W)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_tree.bind("<<TreeviewSelect>>", self.display_history_detail)

        detail_frame = ttk.LabelFrame(main_frame, text="상세 정보", style="History.TLabelframe")
        detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5,0))
        
        self.detail_text = tk.Text(detail_frame, wrap=tk.WORD, state=tk.DISABLED, height=20, width=60, bg="#ECEFF1", relief="sunken", borderwidth=1)
        detail_text_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_text_scroll.set)
        
        detail_text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.load_history_list()

    def load_history_list(self):
        for i in self.history_tree.get_children():
            self.history_tree.delete(i)
        history_items = load_history_summary()
        for item in history_items:
            self.history_tree.insert("", tk.END, iid=item[0], values=item)

    def display_history_detail(self, event=None):
        selected_item = self.history_tree.focus()
        if not selected_item:
            return
        
        history_id_str = self.history_tree.item(selected_item, "values")[0] 
        try:
            history_id = int(history_id_str)
        except ValueError:
            messagebox.showerror("오류", "유효하지 않은 History ID입니다.", parent=self)
            return

        inputs, base_results = load_history_detail(history_id)

        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)

        if inputs and base_results:
            display_str = "--- 입력 값 ---\n"
            display_str += f"아이템명: {inputs.get('item_name', 'N/A')}\n"
            display_str += f"가공전폭: {inputs.get('fabric_width_inch', 'N/A')} inch\n"
            display_str += f"가공중량값: {inputs.get('proc_weight_input_value', 'N/A')} {inputs.get('proc_weight_input_unit', 'N/A')}\n"
            
            display_str += "\n원사 정보:\n"
            for idx, yarn in enumerate(inputs.get('yarns_data', [])):
                display_str += f"  - {yarn.get('display_name_in_combobox','원사 정보 N/A')} ({yarn.get('ratio_pct','N/A')}%)\n"
                display_str += f"    단가: {yarn.get('price_val','N/A')} {yarn.get('price_currency','N/A')}/{yarn.get('price_unit','N/A')}, 품질: {yarn.get('quality','N/A')}\n"


            display_str += f"\nLoss: 제직 {inputs.get('weaving_loss_pct','N/A')}%, 염색 {inputs.get('dyeing_loss_pct','N/A')}%, 지연 {inputs.get('delay_loss_pct','N/A')}%\n"
            display_str += f"제직료: {inputs.get('weaving_fee_krw_kg','N/A')} 원/kg\n"
            display_str += f"염색료: {inputs.get('dyeing_fee_krw_kg','N/A')} 원/kg\n"
            display_str += f"기준환율: {inputs.get('base_exchange_rate_krw_usd','N/A')} 원/$\n"
            
            display_str += "\n기타 비용:\n"
            for oc in inputs.get('other_costs', []):
                display_str += f"  - {oc.get('description','N/A')}: {oc.get('amount','N/A')} {oc.get('currency','N/A')}/yd\n"
            
            display_str += f"\n수주단가: ${inputs.get('selling_price_usd_yd','N/A'):.2f}/yd\n" 

            display_str += "\n--- 기준환율 적용 결과 ---\n"
            details = base_results.get('details', {})
            if "yarn_cost_components_usd_yd" in details and details["yarn_cost_components_usd_yd"]:
                display_str += "원사 구성 비용:\n"
                for yarn_comp in details["yarn_cost_components_usd_yd"]:
                    display_str += f"  - {yarn_comp['name']} ({yarn_comp['ratio']}%): ${yarn_comp['cost_contrib_usd_yd']:.2f}/yd\n"
                display_str += f"총 원사비용 ($/yd): ${details['total_yarn_cost_usd_yd']:.2f}\n"
            else:
                 display_str += f"원사비용 ($/yd): ${details.get('cost_yarn_usd_yd', details.get('total_yarn_cost_usd_yd',0)):.2f}\n"
            
            display_str += f"제직비용 ($/yd): ${details.get('cost_weaving_usd_yd',0):.2f}\n"
            display_str += f"염색비용 ($/yd): ${details.get('cost_dyeing_usd_yd',0):.2f}\n"
            display_str += f"기타비용 합계 ($/yd): ${details.get('total_other_costs_usd_yd',0):.2f}\n"
            display_str += f"(계산 시 사용된 가공중량: {details.get('final_proc_weight_gyd_used', 'N/A'):.2f} g/yd)\n"
            display_str += "-------------------------------------\n"
            display_str += f"NET 단가 ($/yd): ${base_results.get('net_cost_usd_yd',0):.2f}\n"
            margin_display = f"{base_results.get('margin_pct',0):.2f}%" if isinstance(base_results.get('margin_pct'), (int, float)) else str(base_results.get('margin_pct','N/A'))
            display_str += f"마진 (%): {margin_display}\n"
            
            self.detail_text.insert(tk.END, display_str)
        else:
            self.detail_text.insert(tk.END, "상세 정보를 불러올 수 없습니다.")
        
        self.detail_text.config(state=tk.DISABLED)


class FabricCostCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("원단 원가 계산기")
        self.root.geometry("1160x850") 

        ensure_default_yarns_in_json() 
        init_history_db() 

        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        style.configure("TFrame", background="#E8F5E9")
        style.configure("TLabel", background="#E8F5E9", foreground="#004D40")
        style.configure("TButton", background="#66BB6A", foreground="white", borderwidth=1, font=('Helvetica', 9))
        style.map("TButton", background=[('active', '#4CAF50')])
        style.configure("TEntry", fieldbackground="#FFFFFF", foreground="#004D40", padding=2)
        
        style.map('TCombobox', 
                  selectbackground=[('readonly', 'systemHighlight'), ('!readonly', 'systemHighlight')], # 시스템 기본 선택 배경색
                  selectforeground=[('readonly', 'systemHighlightText'), ('!readonly', 'systemHighlightText')], # 시스템 기본 선택 글자색
                  fieldbackground=[('readonly', '#FFFFFF')]) 
        
        style.configure("TRadiobutton", background="#E8F5E9", foreground="#004D40")
        style.configure("Treeview", fieldbackground="#FFFFFF", foreground="#004D40", rowheight=25)
        style.configure("Treeview.Heading", background="#A5D6A7", foreground="#004D40", font=('Helvetica', 10, 'bold'))
        style.configure("TLabelframe", background="#E8F5E9", bordercolor="#00796B", relief="groove")
        style.configure("TLabelframe.Label", background="#A5D6A7", foreground="#004D40", padding=3, font=('Helvetica', 9, 'bold'))
        style.configure("Small.TButton", padding=(1,1), font=('Helvetica', 7))
        style.configure("Accent.TButton", background="#00796B", foreground="white", font=('Helvetica', 10, 'bold'), padding=5)
        style.map("Accent.TButton", background=[('active', '#004D40')])

        self.other_costs_entries = []
        self.db_yarn_data_cache = {} 
        self.yarn_input_rows = [] 

        self.setup_ui()
        self.load_yarns_from_db_to_combobox_options() 
        self._add_yarn_input_row() 

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        input_outer_frame = ttk.Frame(main_frame)
        input_outer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5)) 
        
        input_canvas = tk.Canvas(input_outer_frame, bg="#E8F5E9", highlightthickness=0)
        input_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        input_scrollbar = ttk.Scrollbar(input_outer_frame, orient=tk.VERTICAL, command=input_canvas.yview)
        input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        input_canvas.configure(yscrollcommand=input_scrollbar.set)
        
        self.scrollable_input_frame = ttk.Frame(input_canvas)
        input_canvas.create_window((0,0), window=self.scrollable_input_frame, anchor="nw")
        
        self.scrollable_input_frame.bind("<Configure>", lambda e: input_canvas.configure(scrollregion=input_canvas.bbox("all")))

        row_idx = 0

        top_button_frame = ttk.Frame(self.scrollable_input_frame)
        top_button_frame.grid(row=row_idx, column=0, padx=5, pady=(5,10), sticky="ew", columnspan=2)
        ttk.Button(top_button_frame, text="원사 DB 관리 (JSON)", command=self.open_yarn_db_manager).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(top_button_frame, text="원가 계산 History", command=self.open_history_window).pack(side=tk.LEFT, fill=tk.X, expand=True) 
        row_idx +=1


        item_frame = ttk.LabelFrame(self.scrollable_input_frame, text="기본 정보")
        item_frame.grid(row=row_idx, column=0, padx=5, pady=5, sticky="ew", columnspan=2)
        row_idx += 1

        ttk.Label(item_frame, text="아이템 이름:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.item_name_var = tk.StringVar(value="CPEM(60-147M)")
        ttk.Entry(item_frame, textvariable=self.item_name_var, width=30).grid(row=0, column=1, padx=5, pady=3, sticky="ew", columnspan=3)

        ttk.Label(item_frame, text="가공 전폭 (inch):").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.fabric_width_var = tk.DoubleVar(value=60)
        ttk.Entry(item_frame, textvariable=self.fabric_width_var, width=10).grid(row=1, column=1, padx=5, pady=3, sticky="w")
        
        ttk.Label(item_frame, text="가공 중량 값:").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.proc_weight_value_var = tk.DoubleVar(value=205)
        ttk.Entry(item_frame, textvariable=self.proc_weight_value_var, width=10).grid(row=2, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(item_frame, text="가공 중량 단위:").grid(row=2, column=2, padx=5, pady=3, sticky="w")
        self.proc_weight_unit_var = tk.StringVar(value="g/yd")
        proc_unit_frame = ttk.Frame(item_frame)
        proc_unit_frame.grid(row=2, column=3, sticky="w", padx=5)
        ttk.Radiobutton(proc_unit_frame, text="g/yd", variable=self.proc_weight_unit_var, value="g/yd").pack(side=tk.LEFT)
        ttk.Radiobutton(proc_unit_frame, text="g/sqm", variable=self.proc_weight_unit_var, value="g/sqm").pack(side=tk.LEFT, padx=(5,0))

        yarn_header_frame = ttk.Frame(self.scrollable_input_frame)
        yarn_header_frame.grid(row=row_idx, column=0, padx=5, pady=(10,2), sticky="ew", columnspan=2)
        yarn_header_frame.columnconfigure(1, weight=1) 
        
        ttk.Label(yarn_header_frame, text="원사 정보 (혼용 가능)", font=('Helvetica', 9, 'bold')).grid(row=0, column=0, sticky="w")
        ttk.Button(yarn_header_frame, text="원사 추가 (+)", command=self._add_yarn_input_row, width=12).grid(row=0, column=1, sticky="e", padx=5)
        row_idx +=1

        self.yarn_rows_container = ttk.Frame(self.scrollable_input_frame) 
        self.yarn_rows_container.grid(row=row_idx, column=0, padx=5, pady=0, sticky="ew", columnspan=2)
        row_idx += 1
        
        loss_frame = ttk.LabelFrame(self.scrollable_input_frame, text="Loss (%)")
        loss_frame.grid(row=row_idx, column=0, padx=5, pady=5, sticky="ew", columnspan=2)
        row_idx += 1
        
        ttk.Label(loss_frame, text="제직 Loss (%):").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.weaving_loss_var = tk.DoubleVar(value=2)
        ttk.Entry(loss_frame, textvariable=self.weaving_loss_var, width=8).grid(row=0, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(loss_frame, text="염색 Loss (%):").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.dyeing_loss_var = tk.DoubleVar(value=4)
        ttk.Entry(loss_frame, textvariable=self.dyeing_loss_var, width=8).grid(row=1, column=1, padx=5, pady=3, sticky="w")
        
        ttk.Label(loss_frame, text="지연 Loss (%):").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.delay_loss_var = tk.DoubleVar(value=6)
        ttk.Entry(loss_frame, textvariable=self.delay_loss_var, width=8).grid(row=2, column=1, padx=5, pady=3, sticky="w")

        proc_frame = ttk.LabelFrame(self.scrollable_input_frame, text="가공비 및 환율")
        proc_frame.grid(row=row_idx, column=0, padx=5, pady=5, sticky="ew", columnspan=2)
        row_idx += 1

        ttk.Label(proc_frame, text="제직료 (원화/kg):").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.weaving_fee_krw_kg_var = tk.DoubleVar(value=450)
        ttk.Entry(proc_frame, textvariable=self.weaving_fee_krw_kg_var, width=10).grid(row=0, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(proc_frame, text="염색료 (원화/kg):").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.dyeing_fee_krw_kg_var = tk.DoubleVar(value=1900)
        ttk.Entry(proc_frame, textvariable=self.dyeing_fee_krw_kg_var, width=10).grid(row=1, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(proc_frame, text="기준환율 (원/$):").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.exchange_rate_var = tk.DoubleVar(value=1150)
        ttk.Entry(proc_frame, textvariable=self.exchange_rate_var, width=10).grid(row=2, column=1, padx=5, pady=3, sticky="w")

        other_costs_header_frame = ttk.Frame(self.scrollable_input_frame)
        other_costs_header_frame.grid(row=row_idx, column=0, padx=5, pady=(10,2), sticky="ew", columnspan=2)
        other_costs_header_frame.columnconfigure(1, weight=1) 

        ttk.Label(other_costs_header_frame, text="기타 비용", font=('Helvetica', 9, 'bold')).grid(row=0, column=0, sticky="w")
        ttk.Button(other_costs_header_frame, text="+ 기타 비용 추가", command=self.add_other_cost_field, width=15).grid(row=0, column=1, sticky="e", padx=5)
        row_idx +=1
        
        self.other_costs_frame_container = ttk.Frame(self.scrollable_input_frame) 
        self.other_costs_frame_container.grid(row=row_idx, column=0, padx=5, pady=0, sticky="ew", columnspan=2)
        row_idx += 1
        
        self.add_other_cost_field(description="기타 검사비", amount=0.15, currency="$") 
        self.add_other_cost_field(description="기타 부대비용", amount=0.03, currency="$")


        sell_price_frame = ttk.LabelFrame(self.scrollable_input_frame, text="수주 정보")
        sell_price_frame.grid(row=row_idx, column=0, padx=5, pady=5, sticky="ew", columnspan=2)
        row_idx += 1

        ttk.Label(sell_price_frame, text="수주단가 ($/yd):").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.selling_price_var = tk.DoubleVar(value=1.50)
        ttk.Entry(sell_price_frame, textvariable=self.selling_price_var, width=10).grid(row=0, column=1, padx=5, pady=3, sticky="w")
        
        action_button_frame = ttk.Frame(self.scrollable_input_frame)
        action_button_frame.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=15, sticky="ew")
        ttk.Button(action_button_frame, text="▶ 원가 계산 실행", command=self.calculate_all, style="Accent.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(action_button_frame, text="💾 Excel 저장", command=self.trigger_excel_save).pack(side=tk.LEFT, fill=tk.X, expand=True)
        row_idx += 1

        output_frame = ttk.LabelFrame(main_frame, text="계산 결과")
        output_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=(5, 0), ipadx=5)

        headers = ["적용 환율", "NET 단가 ($/yd)", "마진 (%)"]
        self.results_tree = ttk.Treeview(output_frame, columns=headers, show="headings", height=5)
        for header in headers:
            self.results_tree.heading(header, text=header)
            self.results_tree.column(header, anchor=tk.CENTER, width=130) 
        self.results_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.detailed_results_text = tk.Text(output_frame, height=10, width=45, wrap=tk.WORD, state=tk.DISABLED, bg="#F1F8E9", fg="#004D40", relief="flat", borderwidth=1) 
        self.detailed_results_text.pack(padx=10, pady=(0,10), fill=tk.X, expand=False)

    # AttributeError 해결: open_history_window 메서드 정의
    def open_history_window(self):
        HistoryWindow(self.root)

    def open_yarn_db_manager(self):
        YarnManagementWindow(self.root, self.load_yarns_from_db_to_combobox_options)

    def load_yarns_from_db_to_combobox_options(self):
        all_yarns = load_yarns_from_json()
        self.db_yarn_data_cache = {} 
        sorted_yarn_options = []
        temp_cache_for_sorting = []
        for yarn_data in all_yarns:
            display_desc = generate_yarn_display_description(yarn_data)
            temp_cache_for_sorting.append({
                "display_desc_key": display_desc, "id": yarn_data.get("id"), 
                "price_value": yarn_data.get("price_value"), "price_currency": yarn_data.get("price_currency"), 
                "price_unit": yarn_data.get("price_unit"), "quality": yarn_data.get("quality")})
        temp_cache_for_sorting.sort(key=lambda y: y["display_desc_key"].lower())
        for yarn_entry in temp_cache_for_sorting:
            unique_display_key = yarn_entry["display_desc_key"]
            count = 1
            while unique_display_key in self.db_yarn_data_cache: 
                unique_display_key = f"{yarn_entry['display_desc_key']} [{count}]"
                count += 1
            self.db_yarn_data_cache[unique_display_key] = {
                "id": yarn_entry["id"], "단가_금액": yarn_entry["price_value"], 
                "단가_통화": yarn_entry["price_currency"], "단가_단위": yarn_entry["price_unit"], 
                "quality": yarn_entry["quality"]}
            sorted_yarn_options.append(unique_display_key)
        self.yarn_combobox_options = sorted_yarn_options 
        for row_data in self.yarn_input_rows: 
            current_selection = row_data['selection_var'].get() 
            row_data['selection_combo']['values'] = self.yarn_combobox_options
            if current_selection in self.yarn_combobox_options: 
                row_data['selection_var'].set(current_selection)
            elif self.yarn_combobox_options: 
                 row_data['selection_var'].set(self.yarn_combobox_options[0])
            else: 
                row_data['selection_var'].set("")
            self._on_yarn_row_selected(row_data) 

    def _add_yarn_input_row(self):
        row_frame = ttk.Frame(self.yarn_rows_container)
        row_frame.pack(fill=tk.X, pady=2, padx=2) 

        yarn_id_var = tk.IntVar()
        selection_var = tk.StringVar()
        price_var = tk.DoubleVar()
        currency_var = tk.StringVar() 
        unit_var = tk.StringVar()     
        quality_var = tk.StringVar()  
        ratio_var = tk.DoubleVar(value=100.0 if not self.yarn_input_rows else 0.0) 

        row_data = {"frame": row_frame, "id_var": yarn_id_var, "selection_var": selection_var, 
                    "price_var": price_var, "currency_var": currency_var, "unit_var": unit_var, 
                    "quality_var": quality_var, "ratio_var": ratio_var}

        ttk.Label(row_frame, text="원사:", width=5).pack(side=tk.LEFT, padx=(0,2)) 
        combo = ttk.Combobox(row_frame, textvariable=selection_var, 
                             values=getattr(self, 'yarn_combobox_options', []), 
                             width=38, state="readonly") 
        combo.pack(side=tk.LEFT, padx=(0,5))
        combo.bind("<<ComboboxSelected>>", lambda e, rd=row_data: self._on_yarn_row_selected(rd))
        row_data['selection_combo'] = combo

        ttk.Label(row_frame, text="단가:", width=5).pack(side=tk.LEFT, padx=(0,2)) 
        ttk.Entry(row_frame, textvariable=price_var, width=7).pack(side=tk.LEFT, padx=(0,2)) 
        
        price_display_label = ttk.Label(row_frame, text="$ / lb", width=7) 
        price_display_label.pack(side=tk.LEFT, padx=(0,5))
        row_data['price_display_label'] = price_display_label
        
        ratio_label = ttk.Label(row_frame, text="비율(%):", width=6) 
        ratio_entry = ttk.Entry(row_frame, textvariable=ratio_var, width=5) 
        row_data['ratio_label_widget'] = ratio_label
        row_data['ratio_entry_widget'] = ratio_entry

        remove_btn = ttk.Button(row_frame, text="X", width=2, style="Small.TButton",
                                command=lambda rd=row_data: self._remove_yarn_input_row(rd))
        remove_btn.pack(side=tk.RIGHT, padx=(5,0)) 

        self.yarn_input_rows.append(row_data)
        self._update_yarn_ratio_visibility() 

        if hasattr(self, 'yarn_combobox_options') and self.yarn_combobox_options: 
            test_yarn_name_base = "Test Yarn" 
            default_set = False
            for option in self.yarn_combobox_options:
                if test_yarn_name_base in option:
                    selection_var.set(option)
                    default_set = True
                    break
            if not default_set and self.yarn_combobox_options: 
                 selection_var.set(self.yarn_combobox_options[0])
            self._on_yarn_row_selected(row_data)
        
        self.scrollable_input_frame.update_idletasks()
        if hasattr(self.scrollable_input_frame.master, 'bbox'): 
            self.scrollable_input_frame.master.configure(scrollregion=self.scrollable_input_frame.master.bbox("all"))

    def _remove_yarn_input_row(self, row_data_to_remove):
        if len(self.yarn_input_rows) <= 1 and row_data_to_remove in self.yarn_input_rows:
            messagebox.showwarning("경고", "최소 한 개의 원사 정보는 필요합니다.", parent=self.root)
            return
        row_data_to_remove['frame'].destroy()
        self.yarn_input_rows.remove(row_data_to_remove)
        self._update_yarn_ratio_visibility()

    def _update_yarn_ratio_visibility(self):
        show_ratio = len(self.yarn_input_rows) > 1
        for row_data in self.yarn_input_rows:
            if show_ratio:
                row_data['ratio_label_widget'].pack(side=tk.LEFT, padx=(5,2))
                row_data['ratio_entry_widget'].pack(side=tk.LEFT, padx=(0,5))
            else:
                row_data['ratio_label_widget'].pack_forget()
                row_data['ratio_entry_widget'].pack_forget()
                row_data['ratio_var'].set(100.0) 
        if not show_ratio and self.yarn_input_rows:
            self.yarn_input_rows[0]['ratio_var'].set(100.0)

    def _on_yarn_row_selected(self, row_data):
        selected_display_desc = row_data['selection_var'].get()
        if selected_display_desc and selected_display_desc in self.db_yarn_data_cache:
            yarn_cached_data = self.db_yarn_data_cache[selected_display_desc]
            row_data['id_var'].set(yarn_cached_data.get("id", 0))
            row_data['price_var'].set(yarn_cached_data.get("단가_금액", 0.0))
            row_data['currency_var'].set(yarn_cached_data.get("단가_통화", "$"))
            row_data['unit_var'].set(yarn_cached_data.get("단가_단위", "lb"))
            row_data['quality_var'].set(yarn_cached_data.get("quality", "일반"))
            row_data['price_display_label'].config(text=f"{row_data['currency_var'].get()} / {row_data['unit_var'].get()}")
        else: 
            row_data['id_var'].set(0); row_data['price_var'].set(0.0)
            row_data['currency_var'].set("$"); row_data['unit_var'].set("lb")
            row_data['quality_var'].set("일반"); row_data['price_display_label'].config(text="$ / lb")

    def add_other_cost_field(self, description="", amount=0.0, currency="$"):
        entry_row_idx = len(self.other_costs_entries) + 1
        item_frame = ttk.Frame(self.other_costs_frame_container) 
        item_frame.pack(fill=tk.X, pady=1, padx=2) 

        desc_var = tk.StringVar(value=description)
        amount_var = tk.DoubleVar(value=amount)
        currency_var = tk.StringVar(value=currency)
        ttk.Label(item_frame, text="설명:").pack(side=tk.LEFT, padx=(0,2))
        ttk.Entry(item_frame, textvariable=desc_var, width=15).pack(side=tk.LEFT, padx=(0,5)) 
        ttk.Label(item_frame, text="금액:").pack(side=tk.LEFT, padx=(0,2))
        ttk.Entry(item_frame, textvariable=amount_var, width=8).pack(side=tk.LEFT, padx=(0,5)) 
        currency_combo = ttk.Combobox(item_frame, textvariable=currency_var, values=["$", "원화"], width=5, state="readonly") 
        currency_combo.pack(side=tk.LEFT, padx=(0,2))
        if currency not in ["$", "원화"]: currency_combo.set("$")
        else: currency_combo.set(currency)
        ttk.Label(item_frame, text="/yd").pack(side=tk.LEFT)
        remove_button = ttk.Button(item_frame, text="X", width=2, style="Small.TButton",
                                   command=lambda f=item_frame, entry_dict={'desc':desc_var, 'amount':amount_var, 'currency':currency_var, 'frame':item_frame}: self.remove_other_cost_field(entry_dict))
        remove_button.pack(side=tk.RIGHT, padx=(5,0)) 
        self.other_costs_entries.append({'desc': desc_var, 'amount': amount_var, 'currency': currency_var, 'frame': item_frame})
        if hasattr(self, 'scrollable_input_frame'): self.scrollable_input_frame.update_idletasks()

    def remove_other_cost_field(self, entry_dict_to_remove):
        entry_dict_to_remove['frame'].destroy()
        self.other_costs_entries.remove(entry_dict_to_remove)
        if hasattr(self, 'scrollable_input_frame'): self.scrollable_input_frame.update_idletasks()

    def get_all_inputs(self):
        try:
            inputs = {"item_name": self.item_name_var.get(), "fabric_width_inch": self.fabric_width_var.get(),
                      "proc_weight_input_value": self.proc_weight_value_var.get(),
                      "proc_weight_input_unit": self.proc_weight_unit_var.get(), "yarns_data": [],
                      "weaving_loss_pct": self.weaving_loss_var.get(), "dyeing_loss_pct": self.dyeing_loss_var.get(),
                      "delay_loss_pct": self.delay_loss_var.get(),
                      "weaving_fee_krw_kg": self.weaving_fee_krw_kg_var.get(),
                      "dyeing_fee_krw_kg": self.dyeing_fee_krw_kg_var.get(),
                      "base_exchange_rate_krw_usd": self.exchange_rate_var.get(), "other_costs": [],
                      "selling_price_usd_yd": self.selling_price_var.get()}
            if inputs["proc_weight_input_value"] <= 0: raise ValueError("가공 중량 값은 0보다 커야 합니다.")
            if inputs["proc_weight_input_unit"] == "g/sqm" and inputs["fabric_width_inch"] <= 0:
                raise ValueError("g/sqm 단위 선택 시 가공 전폭은 0보다 커야 합니다.")
            if inputs["base_exchange_rate_krw_usd"] <= 0: raise ValueError("기준환율은 0보다 커야 합니다.")
            total_yarn_ratio = 0
            if not self.yarn_input_rows: raise ValueError("최소 한 개의 원사 정보가 필요합니다.")
            for row_data in self.yarn_input_rows:
                if not row_data['id_var'].get() or row_data['id_var'].get() == 0:
                    raise ValueError("모든 원사 항목에서 원사를 선택해주세요.")
                ratio = row_data['ratio_var'].get()
                if len(self.yarn_input_rows) > 1 and ratio <= 0: 
                    raise ValueError("다중 원사 사용 시, 각 원사의 비율은 0보다 커야 합니다.")
                inputs["yarns_data"].append({"id": row_data['id_var'].get(), "price_val": row_data['price_var'].get(), 
                                            "price_currency": row_data['currency_var'].get(), 
                                            "price_unit": row_data['unit_var'].get(),       
                                            "quality": row_data['quality_var'].get(), "ratio_pct": ratio,
                                            "display_name_in_combobox": row_data['selection_var'].get() 
                                            })
                total_yarn_ratio += ratio
            if len(self.yarn_input_rows) > 1 and abs(total_yarn_ratio - 100.0) > 1e-3: 
                raise ValueError(f"모든 원사 비율의 합이 100%여야 합니다. (현재 합계: {total_yarn_ratio:.2f}%)")
            elif not self.yarn_input_rows: raise ValueError("원사 정보가 없습니다.")
            for entry in self.other_costs_entries:
                inputs["other_costs"].append({"description": entry['desc'].get(), "amount": entry['amount'].get(), "currency": entry['currency'].get()})
            return inputs
        except tk.TclError as e: messagebox.showerror("입력 오류", f"숫자 입력란을 확인해주세요: {e}"); return None
        except ValueError as e: messagebox.showerror("입력 오류", str(e)); return None

    def calculate_single_scenario(self, inputs, current_exchange_rate):
        try:
            proc_weight_input_val = inputs["proc_weight_input_value"]
            proc_weight_input_unit = inputs["proc_weight_input_unit"]
            fabric_width_inch = inputs["fabric_width_inch"]
            proc_weight_gyd = proc_weight_input_val
            if proc_weight_input_unit == "g/sqm":
                if fabric_width_inch <= 0: raise ValueError("g/sqm 변환을 위해 가공 전폭이 필요합니다.")
                proc_weight_gyd = proc_weight_input_val * fabric_width_inch * 0.02322576
            proc_weight_kg_yd = proc_weight_gyd / 1000.0
            loss_multiplier = (1 + inputs["weaving_loss_pct"]/100.0) * (1 + inputs["dyeing_loss_pct"]/100.0) * (1 + inputs["delay_loss_pct"]/100.0)
            total_yarn_cost_usd_yd = 0
            yarn_cost_details_for_display = [] 
            for yarn_input in inputs["yarns_data"]:
                yarn_price_val_live = yarn_input["price_val"] 
                yarn_currency_from_db = yarn_input["price_currency"] 
                yarn_unit_from_db = yarn_input["price_unit"]       
                yarn_ratio_pct = yarn_input["ratio_pct"]
                price_in_usd_original_unit = yarn_price_val_live
                if yarn_currency_from_db == "원화":
                    if current_exchange_rate == 0: raise ValueError("환율 오류(원사).")
                    price_in_usd_original_unit = yarn_price_val_live / current_exchange_rate
                if yarn_unit_from_db == "lb": yarn_price_usd_per_kg_for_this_yarn = price_in_usd_original_unit * 2.20462
                else: yarn_price_usd_per_kg_for_this_yarn = price_in_usd_original_unit
                cost_if_100pct_this_yarn = yarn_price_usd_per_kg_for_this_yarn * proc_weight_kg_yd * loss_multiplier
                weighted_cost_this_yarn = cost_if_100pct_this_yarn * (yarn_ratio_pct / 100.0)
                total_yarn_cost_usd_yd += weighted_cost_this_yarn
                yarn_cost_details_for_display.append({
                    "name": yarn_input.get("display_name_in_combobox", "N/A"), 
                    "id": yarn_input.get("id"), 
                    "price_val_live": yarn_price_val_live,
                    "currency_from_db": yarn_currency_from_db,
                    "unit_from_db": yarn_unit_from_db,
                    "ratio": yarn_ratio_pct,
                    "cost_if_100pct_usd_yd": cost_if_100pct_this_yarn, 
                    "cost_contrib_usd_yd": weighted_cost_this_yarn
                })
            if current_exchange_rate == 0: raise ValueError("환율 오류(가공비).")
            cost_weaving_usd_yd = (inputs["weaving_fee_krw_kg"] * proc_weight_kg_yd) / current_exchange_rate
            cost_dyeing_usd_yd = (inputs["dyeing_fee_krw_kg"] * proc_weight_kg_yd) / current_exchange_rate
            total_other_costs_usd_yd = 0
            for oc in inputs["other_costs"]:
                amount = oc["amount"]
                if oc["currency"] == "원화":
                    if current_exchange_rate == 0: raise ValueError("환율 오류(기타비용).")
                    total_other_costs_usd_yd += amount / current_exchange_rate
                else: total_other_costs_usd_yd += amount
            net_cost_usd_yd = total_yarn_cost_usd_yd + cost_weaving_usd_yd + cost_dyeing_usd_yd + total_other_costs_usd_yd
            margin_pct = 0.0
            if inputs["selling_price_usd_yd"] is not None:
                if net_cost_usd_yd != 0 : margin_pct = ((inputs["selling_price_usd_yd"] - net_cost_usd_yd) / net_cost_usd_yd) * 100
                elif inputs["selling_price_usd_yd"] > 0 : margin_pct = float('inf') 
            return {"net_cost_usd_yd": net_cost_usd_yd, "margin_pct": margin_pct,
                    "details": {"cost_yarn_components_usd_yd": yarn_cost_details_for_display, "total_yarn_cost_usd_yd": total_yarn_cost_usd_yd, 
                                "cost_weaving_usd_yd": cost_weaving_usd_yd, "cost_dyeing_usd_yd": cost_dyeing_usd_yd, 
                                "total_other_costs_usd_yd": total_other_costs_usd_yd, "final_proc_weight_gyd_used": proc_weight_gyd}}
        except ValueError as e: messagebox.showerror("계산 오류", str(e)); return None

    def calculate_all(self):
        inputs = self.get_all_inputs()
        if not inputs: return
        base_rate = inputs["base_exchange_rate_krw_usd"]
        rates_to_calculate = {f"{base_rate - 50:.0f} 원": base_rate - 50, f"{base_rate:.0f} 원": base_rate, f"{base_rate + 50:.0f} 원": base_rate + 50}
        for i in self.results_tree.get_children(): self.results_tree.delete(i)
        self.detailed_results_text.config(state=tk.NORMAL); self.detailed_results_text.delete(1.0, tk.END)
        all_scenario_results, base_rate_details_for_display = [], {}
        calculation_succeeded_for_base_rate = False
        for scenario_label, rate_value in rates_to_calculate.items():
            if rate_value <= 0:
                self.results_tree.insert("", tk.END, values=(scenario_label, "유효하지 않은 환율", "N/A")); continue
            result = self.calculate_single_scenario(inputs, rate_value)
            if result:
                net_cost_display = f"${result['net_cost_usd_yd']:.2f}" 
                margin_display = f"{result['margin_pct']:.2f}%" if isinstance(result['margin_pct'], (int, float)) else str(result['margin_pct'])
                self.results_tree.insert("", tk.END, values=(scenario_label, net_cost_display, margin_display))
                all_scenario_results.append({"scenario": scenario_label, "rate_used": rate_value, **result})
                if abs(rate_value - base_rate) < 1e-9 : 
                    base_rate_details_for_display = result
                    calculation_succeeded_for_base_rate = True 
            else: self.results_tree.insert("", tk.END, values=(scenario_label, "계산 오류", "N/A"))
        if base_rate_details_for_display and 'details' in base_rate_details_for_display:
            details = base_rate_details_for_display['details']
            detail_str = f"--- 기준환율 ({base_rate:.0f}원) 상세 내역 ---\n"
            if "yarn_cost_components_usd_yd" in details and details["yarn_cost_components_usd_yd"]:
                detail_str += "원사 구성 비용:\n"
                for yarn_comp in details["yarn_cost_components_usd_yd"]:
                    detail_str += f"  - {yarn_comp['name']} ({yarn_comp['ratio']}%): ${yarn_comp['cost_contrib_usd_yd']:.2f}/yd\n" 
                detail_str += f"총 원사비용 ($/yd): ${details['total_yarn_cost_usd_yd']:.2f}\n" 
            else: detail_str += f"원사비용 ($/yd): ${details.get('cost_yarn_usd_yd', details.get('total_yarn_cost_usd_yd',0)):.2f}\n" 
            detail_str += f"제직비용 ($/yd): ${details['cost_weaving_usd_yd']:.2f}\n" 
            detail_str += f"염색비용 ($/yd): ${details['cost_dyeing_usd_yd']:.2f}\n" 
            detail_str += f"기타비용 합계 ($/yd): ${details['total_other_costs_usd_yd']:.2f}\n" 
            detail_str += f"(계산 시 사용된 가공중량: {details.get('final_proc_weight_gyd_used', 'N/A'):.2f} g/yd)\n"
            detail_str += "-------------------------------------\n"
            detail_str += f"NET 단가 ($/yd): {base_rate_details_for_display['net_cost_usd_yd']:.2f}\n"
            detail_str += f"수주 단가 ($/yd): {inputs['selling_price_usd_yd']:.2f}\n"
            margin_display_detail = f"{base_rate_details_for_display['margin_pct']:.2f}%" if isinstance(base_rate_details_for_display['margin_pct'], (int, float)) else str(base_rate_details_for_display['margin_pct'])
            detail_str += f"마진 (%): {margin_display_detail}\n"
            self.detailed_results_text.insert(tk.END, detail_str)
        self.detailed_results_text.config(state=tk.DISABLED)
        if calculation_succeeded_for_base_rate and base_rate_details_for_display:
            save_calculation_to_history(inputs["item_name"], inputs, base_rate_details_for_display)
        self.last_calculation_inputs = inputs 
        self.last_calculation_results_by_scenario = all_scenario_results

    def trigger_excel_save(self): 
        if not hasattr(self, 'last_calculation_inputs') or not self.last_calculation_results_by_scenario:
            messagebox.showinfo("데이터 없음", "먼저 계산을 실행해주세요.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 통합 문서", "*.xlsx"), ("모든 파일", "*.*")],
            title="원가계산서 저장",
            initialfile=f"{self.last_calculation_inputs.get('item_name', '원가계산서')}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx")
        if file_path: self.actual_save_to_excel(file_path)

    def actual_save_to_excel(self, destination_file_path):
        inputs = self.last_calculation_inputs
        all_results = self.last_calculation_results_by_scenario
        if not all_results: # Check if the list itself is empty or None
            messagebox.showerror("오류", "계산 결과를 찾을 수 없습니다.")
            return

        try:
            if getattr(sys, 'frozen', False): 
                application_path = os.path.dirname(sys.executable)
            else: 
                application_path = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(application_path, EXCEL_TEMPLATE_FILE)
        except NameError: 
            template_path = EXCEL_TEMPLATE_FILE 


        if not os.path.exists(template_path):
            messagebox.showerror("템플릿 오류", f"Excel 템플릿 파일을 찾을 수 없습니다:\n{template_path}\n\n실행 파일과 같은 폴더에 '{EXCEL_TEMPLATE_FILE}' 파일이 있는지 확인해주세요.")
            return

        try:
            copyfile(template_path, destination_file_path)
            wb = openpyxl.load_workbook(destination_file_path)

            if "COST" in wb.sheetnames:
                sheet_cost = wb["COST"]
                self.fill_cost_sheet(sheet_cost, inputs, all_results) # Pass all scenario results
                # Rename the sheet to the item name
                item_sheet_name = inputs.get("item_name", "CostSheet")
                if item_sheet_name: # Ensure item_name is not empty
                    sheet_cost.title = item_sheet_name
            else: print(f"Warning: Sheet 'COST' not found in template.")

            wb.save(destination_file_path)
            messagebox.showinfo("성공", f"원가계산서가 다음 위치에 저장되었습니다:\n{destination_file_path}")

        except ImportError: messagebox.showerror("라이브러리 오류", "Excel 처리를 위해 'openpyxl'과 'shutil' 라이브러리가 필요합니다.\n설치해주세요: pip install openpyxl")
        except KeyError as e: messagebox.showerror("오류", f"Excel 템플릿 처리 중 오류: {e}\n템플릿의 시트 이름 등을 확인해주세요.")
        except Exception as e: messagebox.showerror("Excel 저장 오류", f"파일 저장 실패: {e}")


    def fill_cost_sheet(self, sheet, inputs, all_scenario_results):
        base_exchange_rate = inputs.get("base_exchange_rate_krw_usd", 1.0) # 기본값 1.0으로 0 나누기 방지
        print(f"DEBUG: Starting fill_cost_sheet. Base exchange rate: {base_exchange_rate}")

        # 1. B2에 item 명
        item_name = inputs.get("item_name", "")
        print(f"DEBUG: Attempting to write to cell: B2 with value: {item_name}")
        sheet['B2'] = item_name

        if base_exchange_rate == 0: # 만약 입력값이 0이면, 계산 불가로 처리
            base_exchange_rate = 1.0 # 또는 오류 메시지 표시

        # 1. 원사 단가1($/lb): C11
        if len(inputs.get("yarns_data", [])) > 0:
            yarn1 = inputs["yarns_data"][0]
            price1_val = yarn1.get("price_val", 0)
            price1_curr = yarn1.get("price_currency", "$")
            price1_unit = yarn1.get("price_unit", "lb")
            
            price1_usd = price1_val
            if price1_curr == "원화":
                price1_usd = price1_val / base_exchange_rate
            
            price1_usd_lb = price1_usd
            if price1_unit == "kg": # kg당 가격을 lb당 가격으로 변환
                price1_usd_lb = price1_usd / 2.20462
            print(f"DEBUG: Attempting to write to cell: C11 with value: {price1_usd_lb}")
            sheet['C11'] = price1_usd_lb
        else:
            sheet['C11'] = "" 

        # 2. 원사 단가2($/lb): C12
        if len(inputs.get("yarns_data", [])) > 1:
            yarn2 = inputs["yarns_data"][1]
            price2_val = yarn2.get("price_val", 0)
            price2_curr = yarn2.get("price_currency", "$")
            price2_unit = yarn2.get("price_unit", "lb")

            price2_usd = price2_val
            if price2_curr == "원화":
                price2_usd = price2_val / base_exchange_rate
            
            price2_usd_lb = price2_usd
            if price2_unit == "kg":
                price2_usd_lb = price2_usd / 2.20462
            print(f"DEBUG: Attempting to write to cell: C12 with value: {price2_usd_lb}")
            sheet['C12'] = price2_usd_lb
        else:
            sheet['C12'] = ""

        # 3. 원사 단가3($/lb): C13
        if len(inputs.get("yarns_data", [])) > 2:
            yarn3 = inputs["yarns_data"][2]
            price3_val = yarn3.get("price_val", 0)
            price3_curr = yarn3.get("price_currency", "$")
            price3_unit = yarn3.get("price_unit", "lb")

            price3_usd = price3_val
            if price3_curr == "원화":
                price3_usd = price3_val / base_exchange_rate
            
            price3_usd_lb = price3_usd
            if price3_unit == "kg":
                price3_usd_lb = price3_usd / 2.20462
            print(f"DEBUG: Attempting to write to cell: C13 with value: {price3_usd_lb}")
            sheet['C13'] = price3_usd_lb
        else:
            sheet['C13'] = ""

        # 2. B4에 혼용률 및 원사명
        yarn_composition_parts = []
        for yarn_data in inputs.get("yarns_data", []):
            ratio = yarn_data.get("ratio_pct", 0)
            name = yarn_data.get("display_name_in_combobox", "N/A")
            if ratio > 0: # 0% 비율은 제외 (선택 사항)
                yarn_composition_parts.append(f"{ratio}% {name}")
        yarn_composition_str = ", ".join(yarn_composition_parts)
        print(f"DEBUG: Attempting to write to cell: B4 with value: {yarn_composition_str}")
        sheet['B4'] = yarn_composition_str

        # 3. I5에 가공폭 + 가공중량
        fabric_width = inputs.get("fabric_width_inch", "N/A")
        proc_weight_val = inputs.get("proc_weight_input_value", "N/A")
        proc_weight_unit = inputs.get("proc_weight_input_unit", "N/A")
        fabric_spec_str = f'{fabric_width}" X {proc_weight_val} {proc_weight_unit.upper()}'
        print(f"DEBUG: Attempting to write to cell: I5 with value: {fabric_spec_str}")
        sheet['I5'] = fabric_spec_str


        # 4. 제직LOSS: I11
        weaving_loss_factor = 1 + (inputs.get("weaving_loss_pct", 0) / 100.0)
        i11_val = weaving_loss_factor
        print(f"DEBUG: Attempting to write to cell: I11 with value: {i11_val}")
        sheet['I11'] = weaving_loss_factor
        # 5. 염색LOSS: K11 (1 + % 형태)
        dyeing_loss_factor = 1 + (inputs.get("dyeing_loss_pct", 0) / 100.0)
        k11_val = dyeing_loss_factor
        print(f"DEBUG: Attempting to write to cell: K11 with value: {k11_val}")
        sheet['K11'] = dyeing_loss_factor
        # 6. 자연LOSS (지연LOSS): M11 (1 + % 형태)
        delay_loss_factor = 1 + (inputs.get("delay_loss_pct", 0) / 100.0)
        m11_val = delay_loss_factor
        print(f"DEBUG: Attempting to write to cell: M11 with value: {m11_val}")
        sheet['M11'] = delay_loss_factor

        # 7. 제직료(원화/kg): C15
        c15_val = inputs.get("weaving_fee_krw_kg", 0)
        print(f"DEBUG: Attempting to write to cell: C15 with value: {c15_val}")
        sheet['C15'] = inputs.get("weaving_fee_krw_kg", 0)
        # 8. 염색료(원화/kg): C19
        c19_val = inputs.get("dyeing_fee_krw_kg", 0)
        print(f"DEBUG: Attempting to write to cell: C19 with value: {c19_val}")
        sheet['C19'] = inputs.get("dyeing_fee_krw_kg", 0)

        other_costs = inputs.get("other_costs", [])
        # 9. 기타비용 설명1: B23, 기타비용1($/yd): D23
        if len(other_costs) > 0:
            oc1 = other_costs[0]
            sheet['B23'] = oc1.get("description", "")
            print(f"DEBUG: Attempting to write to cell: B23 with value: {oc1.get('description', '')}")
            oc1_amount = oc1.get("amount", 0)
            oc1_curr = oc1.get("currency", "$")
            oc1_amount_usd = oc1_amount
            if oc1_curr == "원화":
                oc1_amount_usd = oc1_amount / base_exchange_rate
            print(f"DEBUG: Attempting to write to cell: D23 with value: {oc1_amount_usd}")
            sheet['D23'] = oc1_amount_usd
            
        else:
            sheet['B23'] = ""
            sheet['D23'] = ""
            
        # 10. 기타비용 설명2: B24, 기타비용2($/yd): D24
        if len(other_costs) > 1:
            oc2 = other_costs[1]
            sheet['B24'] = oc2.get("description", "")
            print(f"DEBUG: Attempting to write to cell: B24 with value: {oc2.get('description', '')}")
            oc2_amount = oc2.get("amount", 0)
            oc2_curr = oc2.get("currency", "$")
            oc2_amount_usd = oc2_amount
            if oc2_curr == "원화":
                oc2_amount_usd = oc2_amount / base_exchange_rate
            sheet['D24'] = oc2_amount_usd
            print(f"DEBUG: Attempting to write to cell: D24 with value: {oc2_amount_usd}")
        else:
            sheet['B24'] = ""
            sheet['D24'] = ""

        # 11. 기타비용 설명3: B25, 기타비용3($/yd): D25
        if len(other_costs) > 2:
            oc3 = other_costs[2]
            sheet['B25'] = oc3.get("description", "")
            print(f"DEBUG: Attempting to write to cell: B25 with value: {oc3.get('description', '')}")
            oc3_amount = oc3.get("amount", 0)
            oc3_curr = oc3.get("currency", "$")
            oc3_amount_usd = oc3_amount
            if oc3_curr == "원화":
                oc3_amount_usd = oc3_amount / base_exchange_rate
            sheet['D25'] = oc3_amount_usd
            print(f"DEBUG: Attempting to write to cell: D25 with value: {oc3_amount_usd}")
        else:
            sheet['B25'] = ""
            sheet['D25'] = ""

        # 환율 및 NET 단가
        rate_minus_50_val = base_exchange_rate - 50
        rate_plus_50_val = base_exchange_rate + 50
        
        net1, net2, net3 = "", "", ""
        rate_minus_50_found_val, rate_plus_50_found_val = rate_minus_50_val, rate_plus_50_val # Default to calculated if not found

        for res_scenario in all_scenario_results:
            rate_used = res_scenario.get("rate_used")
            net_cost = res_scenario.get("net_cost_usd_yd", "")
            
            if abs(rate_used - rate_minus_50_val) < 1e-9: 
                net1 = net_cost
                rate_minus_50_found_val = rate_used
            elif abs(rate_used - base_exchange_rate) < 1e-9:
                net2 = net_cost
            elif abs(rate_used - rate_plus_50_val) < 1e-9:
                net3 = net_cost
                rate_plus_50_found_val = rate_used
        
        # # 12. 환율-50원: I15, NET1: C26
        # print(f"DEBUG: Attempting to write to cell: I15 with value: {rate_minus_50_found_val}")
        # sheet['I15'] = rate_minus_50_found_val
        # print(f"DEBUG: Attempting to write to cell: C26 with value: {net1}")
        # sheet['C26'] = net1

        # # 13. 환율: I16, NET2: C27
        # print(f"DEBUG: Attempting to write to cell: I16 with value: {base_exchange_rate}")
        # sheet['I16'] = base_exchange_rate 
        # print(f"DEBUG: Attempting to write to cell: C27 with value: {net2}")
        # sheet['C27'] = net2
        
        # # 14. 환율+50원: I17, NET3: C28
        # print(f"DEBUG: Attempting to write to cell: I17 with value: {rate_plus_50_found_val}")
        # sheet['I17'] = rate_plus_50_found_val
        # print(f"DEBUG: Attempting to write to cell: C28 with value: {net3}")
        # sheet['C28'] = net3

        # 15. 수주단가($/yd): C31
        c31_val = inputs.get("selling_price_usd_yd", 0)
        print(f"DEBUG: Attempting to write to cell: C31 with value: {c31_val}")
        sheet['C31'] = inputs.get("selling_price_usd_yd", 0)
        print(f"DEBUG: Finished fill_cost_sheet.")

if __name__ == '__main__':
    app_root = tk.Tk()
    calculator = FabricCostCalculatorApp(app_root)
    app_root.mainloop()
