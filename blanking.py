import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

# Material database with recommended parameters
CUTTING_PARAMETER = {
    "S45C": {"feed_rate": [400.0, 450.0, 500.0], "spindle_speed": [1500, 1800, 2000], "depth_of_cut": [0.8, 1.0, 1.2]},
    "SS400": {"feed_rate": [380.0, 430.0, 480.0], "spindle_speed": [1400, 1700, 1900], "depth_of_cut": [0.7, 0.9, 1.1]},
    "DC11": {"feed_rate": [350.0, 400.0, 450.0], "spindle_speed": [1300, 1600, 1800], "depth_of_cut": [0.6, 0.8, 1.0]},
}


def tool_back(
    code: list[str], z_init_post: float, safe_tool_distance: float, tool_diameter: float, workpiece_thickness: float
):
    code.append(f"G00 Z{(z_init_post):.2f}")  # Move to safe height
    code.append(
        f"G00 X{-safe_tool_distance - (tool_diameter / 2)} Y{-workpiece_thickness / 2:.2f}"
    )  # Move to starting position (slightly before material)


def start_coolant(code: list[str]):
    code.append("M08")


def stop_coolant(code: list[str]):
    code.append("M09")


def tool_offset(code: list[str], z_height: float):
    code.append(f"G43 H04 Z{z_height}")


def pause_process(code: list[str], spindle_speed: int):
    code.append("M00")  # Program stop
    code.append(f"M03 S{spindle_speed}")  # Spindle on after resume


def debug_message(message: str, just_clean_depth: float, remaining_stock: float, num_passes: int):
    print(f"{message} Cut")
    print(f"Just clean depth: {just_clean_depth:.2f} mm")
    print(f"Remaining stock: {remaining_stock:.2f} mm")
    print(f"Number of adjustment passes: {num_passes}")


def tool_spindle_stop(code: list[str]):
    code.append("M05")  # Spindle stop


def tool_zero_return(code: list[str], all_axis: bool = False, y_z_axis: bool = False):
    if all_axis is True:  # zero return on start and end program
        code.append("G91 G30 Z0.0")
        code.append("G91 G28 Y0.0")
        code.append("G91 G30 X0.0")
    if y_z_axis is True:  # zero return on start of process
        code.append("G91 G28 Z0.0")
        code.append("G91 G28 Y0.0")


def reset_coordinate(code: list[str]):
    code.append("G90 G00 G54 X0.0 Y0.0")


def generate_face_mill_gcode(
    workpiece_long: float = 100.0,  # Long side of material (mm)
    workpiece_short: float = 50.0,  # Short side of material (mm)
    workpiece_thick: float = 20.0,  # Thick side of material (mm)
    parallel_block_long: float = 0.0,  # Parallel block for long side (mm)
    parallel_block_short: float = 0.0,  # Parallel block for short side (mm)
    long_stock_thickness: float = 155.0,  # Long material thickness (mm)
    short_stock_thickness: float = 53.0,  # Short material thickness (mm)
    tool_diameter: float = 63.0,  # Face mill diameter (mm)
    feed_rate: float = 500.0,  # Feed rate (mm/min)
    spindle_speed: int = 2000,  # Spindle speed (RPM)
    depth_of_cut: float = 1.0,  # Depth of cut per pass in adjustment (mm)
    safe_z_distance: float = 20.0,  # Safe Z distance for rapid moves (mm)
    safe_tool_distance: float = 5.0,  # Safe X distance for rapid moves (mm)
    just_clean_fraction: float = 0.1,  # Fraction of stock_thickness for just clean (10% default)
    debug: bool = False,  # Debug switch
):
    ### JUST CLEAN LONG SIDE ###
    # Long side Z-position (top of workpiece_short + safe height)
    z_long_init = workpiece_short + safe_z_distance + parallel_block_long

    # Calculate just_clean_depth as a fraction of stock_thickness
    just_clean_depth = (short_stock_thickness - workpiece_short) * just_clean_fraction
    just_clean_depth = max(0.1, min(just_clean_depth, 1.0))  # Limit between 0.1mm and 0.5mm

    # Remaining stock after just clean
    remaining_stock = (short_stock_thickness - workpiece_short) - just_clean_depth

    # Calculate number of adjustment passes based on remaining stock
    num_passes = int(remaining_stock / depth_of_cut) + (remaining_stock % depth_of_cut > 0)

    spindle_speed = int(spindle_speed)

    if debug is True:
        debug_message("Long", just_clean_depth, remaining_stock, num_passes)

    # Initialize G-code list
    gcode: list[str] = []

    # Header
    gcode.append("%")  # Program start
    gcode.append("O0131")  # Program Number
    gcode.append("G00 G40 G49 G80")  # Rapid Positioning, Cancel offsets
    gcode.append("G21 G90 G54")  # Metric, Absolute, G54 coordinate system
    tool_zero_return(gcode, all_axis=True)
    reset_coordinate(gcode)
    gcode.append("(FACEMILL DIA. 63)")
    gcode.append("M06 T10")  # Tool change to face mill
    gcode.append(f"M03 S{spindle_speed}")  # Spindle start

    tool_offset(gcode, z_long_init)

    # Current Y position and direction for zigzag
    direction = 1  # 1 for forward, -1 for reverse

    gcode.append("(CEKAM SISI PANJANG)")
    gcode.append("(JUST CLEAN SISI PANJANG)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)

    # Just clean pass
    start_coolant(gcode)
    gcode.append(
        f"G01 Z{short_stock_thickness + parallel_block_long - just_clean_depth:.2f} F{feed_rate / 2:.1f}"
    )  # Plunge
    gcode.append(
        f"G01 X{workpiece_long + 5 + (tool_diameter / 2):.2f} Y{-workpiece_thick / 2:.2f} F{feed_rate / 2:.1f}"
    )  # Cut
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)
    stop_coolant(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    pause_process(gcode, spindle_speed)
    reset_coordinate(gcode)
    tool_offset(gcode, z_height=z_long_init)

    ### ADJUSTMENT LONG SIDE ###
    gcode.append("(PUTAR KE SISI BERLAWANAN)")
    gcode.append("(ADJUSTMENT SISI PANJANG)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)
    start_coolant(gcode)
    for pass_num in range(num_passes):
        # Calculate current depth (after just clean)
        current_depth = just_clean_depth + ((pass_num + 1) * depth_of_cut)
        if current_depth > (short_stock_thickness - workpiece_short):
            current_depth = short_stock_thickness - workpiece_short  # Cap at long stock thickness

        # Generate cutting moves
        gcode.append(
            f"G01 Z{short_stock_thickness + parallel_block_long - current_depth:.2f} F{feed_rate / 2:.1f}"
        )  # Plunge
        if direction == 1:
            adjustment_feed_rate = feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            gcode.append(
                f"G01 X{workpiece_long + 5 + (tool_diameter / 2):.2f} Y{-workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = -1
        else:
            adjustment_feed_rate = feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            gcode.append(
                f"G01 X{-tool_diameter / 2 - safe_tool_distance:.2f} Y{-workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = 1
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter, workpiece_thick)
    stop_coolant(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    pause_process(gcode, spindle_speed)
    reset_coordinate(gcode)

    ### JUST CLEAN SHORT SIDE ###
    z_short_init = workpiece_long + safe_z_distance + parallel_block_long  # Adjusted for short side
    tool_offset(gcode, z_height=z_short_init)
    # Calculate just_clean_depth as a fraction of stock_thickness
    just_clean_depth = (long_stock_thickness - workpiece_short) * just_clean_fraction
    just_clean_depth = max(0.1, min(just_clean_depth, 1.0))  # Limit between 0.1mm and 0.5mm

    # Remaining stock after just clean
    remaining_stock = (long_stock_thickness - workpiece_long) - just_clean_depth

    # Calculate number of adjustment passes based on remaining stock
    num_passes = int(remaining_stock / depth_of_cut) + (remaining_stock % depth_of_cut > 0)

    if debug is True:
        debug_message("Short", just_clean_depth, remaining_stock, num_passes)

    direction = 1  # 1 for forward, -1 for reverse

    gcode.append("(CEKAM SISI PENDEK)")
    gcode.append("(JUST CLEAN SISI PENDEK)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter, workpiece_thick)

    # Just clean pass
    start_coolant(gcode)
    gcode.append(
        f"G01 Z{long_stock_thickness + parallel_block_short - just_clean_depth:.2f} F{feed_rate / 2:.1f}"
    )  # Plunge
    gcode.append(
        f"G01 X{workpiece_short + 5 + (tool_diameter / 2):.2f} Y{-workpiece_thick / 2:.2f} F{feed_rate / 2:.1f}"
    )  # Cut
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter, workpiece_thick)
    stop_coolant(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    pause_process(gcode, spindle_speed)
    reset_coordinate(gcode)
    tool_offset(gcode, z_short_init)

    ### ADJUSTMENT SHORT SIDE ###
    gcode.append("(PUTAR KE SISI BERLAWANAN)")
    gcode.append("(ADJUSTMENT SISI PENDEK)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter, workpiece_thick)
    start_coolant(gcode)
    for pass_num in range(num_passes):
        # Calculate current depth (after just clean)
        current_depth = just_clean_depth + ((pass_num + 1) * depth_of_cut)
        if current_depth > (long_stock_thickness - workpiece_long):
            current_depth = long_stock_thickness - workpiece_long  # Cap at short stock thickness

        # Generate cutting moves
        gcode.append(
            f"G01 Z{long_stock_thickness + parallel_block_short - current_depth:.2f} F{feed_rate / 2:.1f}"
        )  # Plunge
        if direction == 1:
            adjustment_feed_rate = feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            gcode.append(
                f"G01 X{workpiece_short + 5 + (tool_diameter / 2):.2f} Y{-workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = -1
        else:
            adjustment_feed_rate = feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            gcode.append(
                f"G01 X{-tool_diameter / 2 - safe_tool_distance:.2f} Y{-workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = 1

    # Program end
    stop_coolant(gcode)
    tool_spindle_stop(gcode)
    tool_zero_return(gcode, y_z_axis=True)
    gcode.append("M30")  # Program end
    gcode.append("%")  # End of file

    return gcode


def save_gcode_to_file(gcode_lines: list[str], filename: str = "face_mill.nc"):
    """Save G-code to a file"""
    with open(filename, "w") as f:
        for line in gcode_lines:
            f.write(line + "\n")


class GCodeGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatic Blanking")
        self.root.geometry("300x450")  # Increased height to accommodate material selection

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W + tk.E + tk.N + tk.S))

        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W + tk.E + tk.N + tk.S))

        # Tab 1: Workpiece Settings
        workpiece_frame = ttk.Frame(notebook, padding="5")
        notebook.add(workpiece_frame, text="Workpiece Settings")

        # Tab 2: Tool Settings
        tool_frame = ttk.Frame(notebook, padding="5")
        notebook.add(tool_frame, text="Tool Settings")

        # Parameters and their default values
        self.parameters = {
            "workpiece_long": [150.0, "Panjang Blank"],
            "workpiece_short": [50.0, "Lebar Blank"],
            "workpiece_thick": [20.0, "Tebal Blank"],
            "parallel_block_long": [0.0, "Parallel Block Panjang"],
            "parallel_block_short": [0.0, "Parallel Block Pendek"],
            "long_stock_thickness": [155.0, "Panjang Aktual"],
            "short_stock_thickness": [53.0, "Lebar Aktual"],
            "tool_diameter": [60.0, "Diameter Tool"],
            "feed_rate": [410.0, "Feed Rate"],
            "spindle_speed": [1500.0, "Kecepatan Spindle"],
            "depth_of_cut": [1.0, "Depth of Cut"],
            "safe_z_distance": [50.0, "Safe Z Distance"],
            "safe_tool_distance": [5.0, "Safe X Distance"],
            "just_clean_fraction": [0.1, "Just Clean Fraction"],
            "debug": False,
        }

        # Split parameters into two groups
        workpiece_params = [
            "workpiece_long",
            "workpiece_short",
            "workpiece_thick",
            "parallel_block_long",
            "parallel_block_short",
            "long_stock_thickness",
            "short_stock_thickness",
        ]
        tool_params = [
            "tool_diameter",
            "feed_rate",
            "spindle_speed",
            "depth_of_cut",
            "safe_z_distance",
            "safe_tool_distance",
            "just_clean_fraction",
        ]

        # Entries and Comboboxes dictionary
        self.entries = {}

        # Workpiece Settings Tab
        row = 0
        # Material Selection
        ttk.Label(workpiece_frame, text="Material", width=20, anchor="e").grid(row=row, column=0, pady=2, padx=2)
        self.material_var = tk.StringVar(value="S45C")
        material_combo = ttk.Combobox(
            workpiece_frame,
            textvariable=self.material_var,
            values=list(CUTTING_PARAMETER.keys()),
            state="readonly",
            width=10,
        )
        material_combo.grid(row=row, column=1, sticky=(tk.W + tk.E), pady=2)
        material_combo.bind("<<ComboboxSelected>>", self.update_material_params)
        row += 1

        for param in self.parameters:
            if param in workpiece_params:
                label_text = self.parameters[param][1]
                ttk.Label(workpiece_frame, text=f"{label_text}", width=20, anchor="e").grid(
                    row=row, column=0, pady=2, padx=2
                )
                self.entries[param] = ttk.Entry(workpiece_frame, width=10)
                self.entries[param].grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
                self.entries[param].insert(0, str(self.parameters[param][0]))

                units = "mm" if "fraction" not in param else "%"
                ttk.Label(workpiece_frame, text=units, width=10).grid(row=row, column=2, sticky=tk.W, pady=2)
                row += 1

        # Tool Settings Tab
        row = 0

        # Tool parameters
        for param in self.parameters:
            if param in tool_params:
                label_text = self.parameters[param][1]
                ttk.Label(tool_frame, text=f"{label_text}", width=20, anchor="e").grid(
                    row=row, column=0, pady=2, padx=2
                )

                if param in ["feed_rate", "spindle_speed", "depth_of_cut"]:
                    # Use Combobox for these parameters
                    self.entries[param] = ttk.Combobox(tool_frame, width=10, state="readonly")
                    self.update_combo_values(param, "S45C")  # Default material
                else:
                    # Use Entry for other parameters
                    self.entries[param] = ttk.Entry(tool_frame, width=10)
                    self.entries[param].insert(0, str(self.parameters[param][0]))

                self.entries[param].grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)

                units = "mm" if "fraction" not in param else "%"
                if param == "feed_rate":
                    units = "mm/min"
                elif param == "spindle_speed":
                    units = "RPM"
                ttk.Label(tool_frame, text=units, width=10).grid(row=row, column=2, sticky=tk.W, pady=2)
                row += 1

        # Add Debug checkbox
        self.debug_var = tk.BooleanVar(value=self.parameters["debug"])
        debug_check = ttk.Checkbutton(
            tool_frame,
            text="Debug Mode",
            variable=self.debug_var,
            onvalue=True,
            offvalue=False,
        )
        debug_check.grid(row=row, column=0, columnspan=3, pady=2, sticky=tk.W)

        # Filename entry
        ttk.Label(main_frame, text="Output Filename").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.filename_entry = ttk.Entry(main_frame, width=25)
        self.filename_entry.grid(row=2, column=0, sticky=(tk.W + tk.E), pady=2)
        self.filename_entry.insert(0, "facemill_zigzag")

        # Generate button
        self.generate_btn = ttk.Button(main_frame, text="Generate NC Program", command=self.generate_gcode)
        self.generate_btn.grid(row=3, column=0, sticky=tk.W, pady=20)

        # Status label
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=4, column=0, columnspan=3)

        # Configure column weights
        main_frame.columnconfigure(1, weight=1)
        workpiece_frame.columnconfigure(1, weight=1)
        tool_frame.columnconfigure(1, weight=1)

    def update_combo_values(self, param, material):
        """Update combobox values based on selected material"""
        values = CUTTING_PARAMETER[material][param]
        self.entries[param]["values"] = values
        self.entries[param].set(values[1])  # Set to middle value by default

    def update_material_params(self, event):
        """Update all material-dependent parameters when material changes"""
        material = self.material_var.get()
        for param in ["feed_rate", "spindle_speed", "depth_of_cut"]:
            self.update_combo_values(param, material)

    def generate_gcode(self):
        try:
            # Get parameters from entries
            params = {}
            for param in self.parameters:
                if param == "debug":
                    params[param] = self.debug_var.get()
                else:
                    value = float(self.entries[param].get())
                    if value < 0 and param[:8] == "parallel":
                        raise ValueError(f"{param.replace('_', ' ').title()} must be positive or zero")
                    elif value <= 0 and param[:8] != "parallel":
                        raise ValueError(f"{param.replace('_', ' ').title()} must be positive and not zero")
                    params[param] = value

            # Generate G-code
            gcode = generate_face_mill_gcode(**params)
            current_date = datetime.now().strftime("%Y%m%d")
            filename = self.filename_entry.get()
            if not filename.endswith(".nc"):
                filename += ".nc"
            filename = f"{current_date}_{filename}"
            save_gcode_to_file(gcode, filename)

            # Show generated G-code in a new window
            self.show_gcode_window(gcode)

            self.status_label.config(text=f"Generated and saved to {filename}")

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def show_gcode_window(self, gcode):
        # Create new window for G-code preview
        preview_window = tk.Toplevel(self.root)
        filename = self.filename_entry.get()
        current_date = datetime.now().strftime("%Y%m%d")
        if not filename.endswith(".nc"):
            filename += ".nc"
        filename = f"{current_date}_{filename}"
        save_gcode_to_file(gcode, filename)
        preview_window.title(f"Preview {filename}")
        preview_window.geometry("400x600")

        # Text widget with both vertical and horizontal scrollbars
        text_frame = ttk.Frame(preview_window, padding="5")
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(text_frame, wrap=tk.NONE, height=20, width=50)
        text_widget.grid(row=0, column=0, sticky=(tk.W + tk.E + tk.N + tk.S))

        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N + tk.S))
        text_widget.configure(yscrollcommand=v_scrollbar.set)

        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W + tk.E))
        text_widget.configure(xscrollcommand=h_scrollbar.set)

        # Insert G-code
        for line in gcode:
            text_widget.insert(tk.END, line + "\n")
        text_widget.config(state=tk.DISABLED)

        # Configure grid weights for resizing
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)


if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeGeneratorGUI(root)
    root.mainloop()
