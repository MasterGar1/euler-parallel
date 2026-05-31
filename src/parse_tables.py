import os
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt

def extract_group_and_label(filename):
    """
    Extracts the group key (e.g., 'p-500000') and the unique iteration 
    label (e.g., 'i-1') from the filename.
    """
    basename = os.path.splitext(os.path.basename(filename))[0]
    
    # Regex to find 'p-XXXXX' and 'i-XXXXX'
    group_match = re.search(r'(p-\d+)', basename)
    iter_match = re.search(r'(i-\d+)', basename)
    
    group_key = group_match.group(1) if group_match else "unknown_group"
    label = get_name(basename)
    
    return group_key, label

def get_name(filename: str):
    """Extracts a clean name from the filename for labeling purposes."""
    if filename.find('i-1') != -1:
        return "Едра"
    elif filename.find('i-2') != -1:
        return "Средна"
    elif filename.find('i-4') != -1:
        return "Фина"
    return filename

def format_value(val):
    """Formats individual cells: cleans integers and rounds floats to 6 decimals."""
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return f"{val:.6f}"
    return str(val)

def generate_styled_table(file_path, df, output_dir):
    """Generates and saves a styled visual table image for an individual CSV."""
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], downcast='integer')
    formatted_df = df.map(format_value)

    table_width = max(6, formatted_df.shape[1] * 1.8)
    table_height = max(2, (formatted_df.shape[0] + 1) * 0.4)
    
    fig, ax = plt.subplots(figsize=(table_width, table_height))
    ax.axis('off')
    
    table = ax.table(
        cellText=formatted_df.values, 
        colLabels=formatted_df.columns, 
        cellLoc='center', 
        loc='center'
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#e5e7eb')
        cell.set_linewidth(0.7)
        if row == 0:
            cell.set_text_props(weight='bold', color='#ffffff')
            cell.set_facecolor('#1f2937')
        else:
            cell.set_facecolor('#f9fafb' if row % 2 == 0 else '#ffffff')
            
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(output_dir, f"table_{base_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

def generate_combined_plots(group_name, datasets, output_dir):
    """
    Generates 3 separate images (Time, Speedup, Efficiency) for a specific group,
    plotting all its matching iteration files together.
    """
    # 1. Create Time Graph
    fig_tp, ax_tp = plt.subplots(figsize=(9, 5.5))
    all_p_values = set()
    has_tp = False
    for label, df in datasets:
        all_p_values.update(df['p'].tolist())
        if 'Tp' in df.columns:
            ax_tp.plot(df['p'], df['Tp'], marker='.', linewidth=2, label=label)
            has_tp = True
        elif 'Tp(1)' in df.columns:
            ax_tp.plot(df['p'], df['Tp(1)'], marker='.', linewidth=2, label=label)
            has_tp = True
            
    if has_tp:
        sorted_p = sorted(list(all_p_values))
        ax_tp.set_xlabel("Брой нишки", fontsize=10, fontweight='bold')
        ax_tp.set_ylabel("Време (наносекунди)", fontsize=10, fontweight='bold')
        ax_tp.set_xticks(sorted_p)
        ax_tp.grid(True, linestyle="--", alpha=0.5)
        ax_tp.legend(title="Грануларност", bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.savefig(os.path.join(output_dir, f"graphs_{group_name}_time.png"), dpi=300, bbox_inches='tight')
    plt.close(fig_tp)

    # 2. Create Speedup Graph
    fig_sp, ax_sp = plt.subplots(figsize=(9, 5.5))
    has_sp = False
    
    for label, df in datasets:
        if 'Sp' in df.columns:
            ax_sp.plot(df['p'], df['Sp'], marker='.', linewidth=2, label=label)
            has_sp = True
            
    if has_sp:
        sorted_p = sorted(list(all_p_values))
        ax_sp.plot(sorted_p, sorted_p, linestyle=':', color='gray', alpha=0.7)
        ax_sp.set_xlabel("Брой нишки", fontsize=10, fontweight='bold')
        ax_sp.set_ylabel("Ускорение", fontsize=10, fontweight='bold')
        ax_sp.set_xticks(sorted_p)
        ax_sp.grid(True, linestyle="--", alpha=0.5)
        ax_sp.legend(title="Грануларност", bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.savefig(os.path.join(output_dir, f"graphs_{group_name}_speedup.png"), dpi=300, bbox_inches='tight')
    plt.close(fig_sp)

    # 3. Create Efficiency Graph
    fig_ep, ax_ep = plt.subplots(figsize=(9, 5.5))
    has_ep = False
    
    for label, df in datasets:
        if 'Ep' in df.columns:
            ax_ep.plot(df['p'], df['Ep'], marker='.', linewidth=2, label=label)
            has_ep = True
            
    if has_ep:
        sorted_p = sorted(list(all_p_values))
        ax_ep.set_xlabel("Брой нишки", fontsize=10, fontweight='bold')
        ax_ep.set_ylabel("Ефективност", fontsize=10, fontweight='bold')
        ax_ep.set_xticks(sorted_p)
        ax_ep.grid(True, linestyle="--", alpha=0.5)
        ax_ep.legend(title="Грануларност", bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.savefig(os.path.join(output_dir, f"graphs_{group_name}_efficiency.png"), dpi=300, bbox_inches='tight')
    plt.close(fig_ep)

def process_directory(directory_path, output_dir="output_results"):
    os.makedirs(output_dir, exist_ok=True)
    csv_files = glob.glob(os.path.join(directory_path, "*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in: {directory_path}")
        return

    # Dictionary to hold data categorized by group key
    # Structure: { 'p-500000': [('i-1', df), ('i-2', df)], 'p-1000000': [...] }
    groups = {}

    for file_path in csv_files:
        group_key, label = extract_group_and_label(file_path)
        
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

        if df.empty or 'p' not in df.columns:
            continue
            
        # Ensure x-axis sequence sorts sequentially 
        df = df.sort_values(by='p').reset_index(drop=True)
        
        # 1. Output the beautiful table image right away
        generate_styled_table(file_path, df, output_dir)
        
        # 2. Add to group records for graph stitching later
        groups.setdefault(group_key, []).append((label, df))

    # Process records to render independent multi-line files grouped by "p-"
    for group_name, datasets in groups.items():
        print(f"Generating combined comparison graphs for group: {group_name}...")
        generate_combined_plots(group_name, datasets, output_dir)

    print(f"\nExecution finished! Check the '{output_dir}' directory for outputs.")

if __name__ == "__main__":
    target_directory = "C:/Users/GIGABYTE/Desktop/UNI/Semester-6/SPO/Project/results"
    process_directory(target_directory)