"""Conductance over Time Plot

Plots conductance values at different time points (1s, 5s, 10s) from CSV data.
Includes relative-change filtering (default 5%) and a histogram of conductance
relative-change for outliers.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# User-configurable color palette for plots
COLORS = {
    'conductance_sample': 'wheat',
    'conductance_avg_trend': 'orange',
    'conductance_avg_trend_marker': 'orange',
    'conductance_annotation': 'black',
    'resistance_sample': 'lightsteelblue',
    'resistance_avg_trend': 'cornflowerblue',
    'resistance_avg_trend_marker': 'cornflowerblue',
    'resistance_annotation': 'black',
}

FONT_SIZES = {
    'legend': 14,
    'tick_label': 16,
}

ANNOTATION_OFFSET_PTS = 4


def plot_conductance_over_time(csv_file, rel_threshold=0.1, hist_bin_width_us=5.0):
    """Load CSV, filter by conductance relative change, plot conductance before/after, and save figures.

    This version removes resistance completely and focuses only on conductance.
    It keeps annotations (average changes and standard-deviation boxes) for both
    the BEFORE and AFTER subplots.
    """
    try:
        print(f"Loading CSV file: {csv_file}")
        data = pd.read_csv(csv_file, skiprows=1, header=None)

        data = data.head(1000)
        print(f"Loaded data shape: {data.shape}")

        required_cols = 27
        if data.shape[1] < required_cols:
            print(f"WARNING: CSV only has {data.shape[1]} columns, need >= {required_cols}")
            return

        # Extract and convert units (keep same indices as original script)
        conductance_1s = np.abs(data.iloc[:, 14].to_numpy(dtype=float)) * 1e6
        conductance_2s = np.abs(data.iloc[:, 19].to_numpy(dtype=float)) * 1e6
        conductance_3s = np.abs(data.iloc[:, 24].to_numpy(dtype=float)) * 1e6
        conductance_4s = np.abs(data.iloc[:, 29].to_numpy(dtype=float)) * 1e6
        conductance_5s = np.abs(data.iloc[:, 34].to_numpy(dtype=float)) * 1e6
        conductance_6s = np.abs(data.iloc[:, 39].to_numpy(dtype=float)) * 1e6
        conductance_7s = np.abs(data.iloc[:, 44].to_numpy(dtype=float)) * 1e6
        conductance_8s = np.abs(data.iloc[:, 49].to_numpy(dtype=float)) * 1e6
        conductance_9s = np.abs(data.iloc[:, 54].to_numpy(dtype=float)) * 1e6
        conductance_10s = np.abs(data.iloc[:, 59].to_numpy(dtype=float)) * 1e6

        print(f"Conductance sample (µS): {conductance_1s[:5]}")

        time_points = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), sharey=True)

        # compute per-sample range and mean
        c_stack = np.vstack([conductance_1s, conductance_2s, conductance_3s, conductance_4s, conductance_5s, conductance_6s, conductance_7s, conductance_8s, conductance_9s, conductance_10s])
        cond_max = np.nanmax(c_stack, axis=0)
        cond_min = np.nanmin(c_stack, axis=0)
        cond_range = cond_max - cond_min
        cond_mean = np.nanmean(c_stack, axis=0)

        EPS = 1e-12
        cond_denom = np.maximum(np.abs(cond_mean), EPS)

        cond_rel = cond_range / cond_denom

        total_original = cond_rel.size
        cond_outliers = np.sum(cond_rel > rel_threshold)

        print(f"Filtering samples with relative change > {rel_threshold*100:.1f}% (conductance)")
        print(f"Original samples: {total_original}")
        print(f"Conductance outliers (> {rel_threshold*100:.1f}%): {cond_outliers} ({cond_outliers/total_original:.2%})")

        # Identify outliers based on conductance only
        outlier_mask = (cond_rel > rel_threshold)

        # Save cleaned CSV (without outliers)
        keep_mask_csv = (~outlier_mask) & np.isfinite(cond_rel)
        # Do not copy the source file's second or third physical rows to the output.
        keep_mask_csv[:2] = False
        cleaned_data = data[keep_mask_csv].copy()
        
        # Generate output filename based on input filename
        base_name = os.path.splitext(os.path.basename(csv_file))[0]
        cleaned_csv_filename = f"{base_name}_cleaned.csv"
        
        # Save with same format as original (skip first row will be handled by re-adding header)
        # Read original first line as header
        with open(csv_file, 'r') as f:
            header_line = f.readline().strip()
        
        # Write cleaned CSV
        with open(cleaned_csv_filename, 'w') as f:
            f.write(header_line + '\n')
        cleaned_data.to_csv(cleaned_csv_filename, mode='a', header=False, index=False)
        
        print(f"\nSaved cleaned CSV (outliers removed): '{cleaned_csv_filename}'")
        print(f"  Original rows: {len(data)}, Cleaned rows: {len(cleaned_data)}, Removed: {len(data) - len(cleaned_data)}")
        
        # Also save a version that removes outliers AND their measurement groups
        # Each group consists of 3 measurements: "first", "after", "final" (column 1)
        # If any measurement in a group is an outlier, remove the entire group
        try:
            measurement_type = data.iloc[:, 1].astype(str).str.strip().str.lower()
        except Exception:
            measurement_type = pd.Series(['unknown'] * len(data))
        
        outlier_indices = np.where(outlier_mask)[0]
        extended_outlier_mask = outlier_mask.copy()
        
        # For each outlier, find its measurement group and mark all 3 measurements
        for idx in outlier_indices:
            meas_type = measurement_type.iloc[idx]
            
            # Determine the start of this group based on measurement type
            if meas_type == 'first':
                group_start = idx
            elif meas_type == 'after':
                group_start = idx - 1
            elif meas_type == 'final':
                group_start = idx - 2
            else:
                # Unknown type, skip group removal
                continue
            
            # Mark all 3 measurements in this group (if they exist)
            for offset in range(3):
                group_idx = group_start + offset
                if 0 <= group_idx < len(extended_outlier_mask):
                    extended_outlier_mask[group_idx] = True
        
        # Count how many additional samples were marked
        neighbors_removed = np.sum(extended_outlier_mask) - np.sum(outlier_mask)
        
        # Save extended cleaned CSV (without outliers and their neighbors)
        keep_mask_extended = (~extended_outlier_mask) & np.isfinite(cond_rel)
        cleaned_data_extended = data[keep_mask_extended].copy()
        
        cleaned_csv_extended_filename = f"{base_name}_cleaned_iterative_data_extended_second_iteration.csv"
        
        # Write extended cleaned CSV
        #with open(cleaned_csv_extended_filename, 'w') as f:
        #    f.write(header_line + '\n')
        #cleaned_data_extended.to_csv(cleaned_csv_extended_filename, mode='a', header=False, index=False)
        
        print(f"\nSaved extended cleaned CSV (outliers + neighbors removed): '{cleaned_csv_extended_filename}'")
        print(f"  Original rows: {len(data)}, Cleaned rows: {len(cleaned_data_extended)}, Removed: {len(data) - len(cleaned_data_extended)}")
        print(f"  (Outliers: {np.sum(outlier_mask)}, Neighbors: {neighbors_removed})")
        
        # Save every 3rd row starting from row 4 (index 3: rows 4, 7, 10, ...) from CLEANED data
        every_third_indices = list(range(2, len(cleaned_data_extended), 3))  # Start at index 3 (row 4), step by 3
        every_third_data = cleaned_data_extended.iloc[every_third_indices].copy()
        
        every_third_filename = f"{base_name}_cleaned_iterative_data_every_third_row_second_iteration.csv"
        
        # Write every 3rd row CSV
        #with open(every_third_filename, 'w') as f:
        #    f.write(header_line + '\n')
        #every_third_data.to_csv(every_third_filename, mode='a', header=False, index=False)
        
        print(f"\nSaved every 3rd row CSV (rows 4, 7, 10, ... from cleaned data): '{every_third_filename}'")
        print(f"  Total rows selected: {len(every_third_data)}")
        
        # Save every 3rd row starting from row 3 (index 2: rows 3, 6, 9, ...) from CLEANED data (one row before)
        every_third_indices_firstpulseafter = list(range(1, len(cleaned_data_extended), 3))  # Start at index 1 (row 3), step by 3
        every_third_data_firstpulseafter = cleaned_data_extended.iloc[every_third_indices_firstpulseafter].copy()
        
        every_third_filename_firstpulseafter = f"{base_name}_cleaned_iterative_data_every_third_row_firstpulseafter_second_iteration.csv"
        
        # Write every 3rd row CSV (firstpulseafter version)
        #with open(every_third_filename_firstpulseafter, 'w') as f:
        #    f.write(header_line + '\n')
        #every_third_data_firstpulseafter.to_csv(every_third_filename_firstpulseafter, mode='a', header=False, index=False)
        
        print(f"Saved every 3rd row CSV (rows 3, 6, 9, ... from cleaned data): '{every_third_filename_firstpulseafter}'")
        print(f"  Total rows selected: {len(every_third_data_firstpulseafter)}")

        # We'll create histograms of the BASELINE conductance (1s) values for outliers.
        try:
            state_col = data.iloc[:, 0].astype(str).str.strip().str.lower()
        except Exception:
            state_col = pd.Series(['unknown'] * len(data))

        cond_baseline = conductance_1s  # already in µS
        cond_baseline_outliers = cond_baseline[outlier_mask]
        state_outliers = state_col.to_numpy()[outlier_mask]

        # Helper to create and save histogram for a given mask and filename
        def _save_hist_for_group(values, group_name, filename):
            if values.size == 0:
                print(f"No outliers for group '{group_name}' — skipping histogram '{filename}'")
                return
            min_edge = np.nanmin(values)
            max_edge = np.nanmax(values)
            start = np.floor(min_edge / hist_bin_width_us) * hist_bin_width_us
            end = (np.ceil(max_edge / hist_bin_width_us) + 1) * hist_bin_width_us
            bins = np.arange(start, end + hist_bin_width_us, hist_bin_width_us)

            plt.figure(figsize=(8, 6))
            plt.hist(values, bins=bins, color=COLORS['conductance_avg_trend'], edgecolor='black')
            plt.xlabel('Conductance (µS)')
            plt.ylabel('Number of outlier samples')
            #plt.title(f"Outlier count by baseline conductance — {group_name} (>{rel_threshold*100:.1f}% relative)")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(filename, dpi=300)
            plt.close()
            print(f"Saved histogram '{filename}' (bin size {hist_bin_width_us} µS) — {values.size} samples")

        _save_hist_for_group(cond_baseline_outliers, 'all', 'conductance_outliers_histogram_second_iteration_candidate_selection.png')

        # Histogram split by set/reset states
        set_mask = np.array([s == 'set' for s in state_outliers], dtype=bool)
        reset_mask = np.array([s == 'reset' for s in state_outliers], dtype=bool)

        cond_set = cond_baseline_outliers[set_mask]
        cond_reset = cond_baseline_outliers[reset_mask]

        _save_hist_for_group(cond_set, 'set', 'conductance_outliers_histogram_set__second_iteration_candidate_selection.png')
        _save_hist_for_group(cond_reset, 'reset', 'conductance_outliers_histogram_reset_second_iteration_candidate_selection.png')

        # --- Outlier regime counts (LCS / Transition / HCS) using baseline (1s) conductance ---
        try:
            total_outliers = int(cond_baseline_outliers.size)
            if total_outliers > 0:
                lcs_mask = cond_baseline_outliers < 45.0
                trans_mask = (cond_baseline_outliers >= 45.0) & (cond_baseline_outliers <= 80.0)
                hcs_mask = cond_baseline_outliers > 80.0

                lcs_count = int(np.sum(lcs_mask))
                trans_count = int(np.sum(trans_mask))
                hcs_count = int(np.sum(hcs_mask))

                lcs_pct = lcs_count / total_outliers * 100.0
                trans_pct = trans_count / total_outliers * 100.0
                hcs_pct = hcs_count / total_outliers * 100.0

                print(f"Outlier baseline regime breakdown (n={total_outliers}):")
                print(f"  LCS (<45 µS):       {lcs_count} ({lcs_pct:.2f}%)")
                print(f"  Transition 45-80:  {trans_count} ({trans_pct:.2f}%)")
                print(f"  HCS (>80 µS):      {hcs_count} ({hcs_pct:.2f}%)")
            else:
                print("No outliers found — regime breakdown skipped.")
        except Exception:
            print("Could not compute outlier regime breakdown (unexpected data)")

        # --- BEFORE: plot all samples ---
        n_before = cond_baseline.size
        for i in range(n_before):
            vals = [
                conductance_1s[i], conductance_2s[i], conductance_3s[i],
                conductance_4s[i], conductance_5s[i], conductance_6s[i],
                conductance_7s[i], conductance_8s[i], conductance_9s[i],
                conductance_10s[i],
            ]
            ax1.plot(time_points, vals, color=COLORS['conductance_sample'], linestyle='-', alpha=0.6, linewidth=1.0)

        avg_before = [np.nanmean(conductance) for conductance in c_stack]
        std_before = [np.nanstd(conductance) for conductance in c_stack]
        ax1.plot(time_points, avg_before, color=COLORS['conductance_avg_trend'], linewidth=3, marker='o', markersize=6, markerfacecolor=COLORS['conductance_avg_trend_marker'], markeredgecolor=COLORS['conductance_avg_trend_marker'], label=f'Avg (n={n_before})')

        #ax1.set_title('Conductance BEFORE outlier removal')
        ax1.set_xlabel('Time (seconds)', fontsize=14)
        ax1.set_ylabel('Conductance (µS)', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=FONT_SIZES['legend'], loc='upper center')
        ax1.set_xticks(time_points)
        ax1.tick_params(axis='both', which='major', labelsize=FONT_SIZES['tick_label'])

        # annotate average changes and standard deviation box
        avg_change_1_to_5_before = avg_before[1] - avg_before[0]
        avg_change_5_to_10_before = avg_before[2] - avg_before[1]
        y_offset = 0.02 * float(np.nanmax(avg_before))
        ax1.annotate(f'Δ = {avg_change_1_to_5_before:.3f} µS', xy=(3, avg_before[0] + avg_change_1_to_5_before/2 + y_offset), fontsize=12, ha='center')
        ax1.annotate(f'Δ = {avg_change_5_to_10_before:.3f} µS', xy=(7, avg_before[1] + avg_change_5_to_10_before/2 + y_offset), fontsize=12, ha='center')

        #sd_lines = [f"{tp}s: {sd:.3f} µS" for tp, sd in zip(time_points, std_before)]
        #sd_text = "Std (µS)\n" + "\n".join(sd_lines)
        #ax1.text(0.98, 0.95, sd_text, transform=ax1.transAxes, ha='right', va='top', fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

        # --- AFTER: plot only non-outliers ---
        keep_mask = (~outlier_mask) & np.isfinite(cond_rel)
        conductances_after = [conductance[keep_mask] for conductance in c_stack]

        n_after = conductances_after[0].size
        for i in range(n_after):
            ax2.plot(
                time_points,
                [conductance[i] for conductance in conductances_after],
                color=COLORS['resistance_sample'],
                linestyle='-',
                alpha=0.8,
                linewidth=1.2,
            )

        if n_after > 0:
            avg_after = [np.nanmean(conductance) for conductance in conductances_after]
            std_after = [np.nanstd(conductance) for conductance in conductances_after]
        else:
            avg_after = avg_before
            std_after = std_before

        ax2.plot(time_points, avg_after, color=COLORS['resistance_avg_trend'], linewidth=3, marker='o', markersize=6, markerfacecolor=COLORS['resistance_avg_trend_marker'], markeredgecolor=COLORS['resistance_avg_trend_marker'], label=f'Avg (n={n_after})')
        #ax2.set_title('Conductance AFTER outlier removal')
        ax2.set_xlabel('Time (seconds)', fontsize=14)
        ax2.set_xticks(time_points)
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=FONT_SIZES['legend'], loc='upper center')

        avg_change_1_to_5_after = avg_after[1] - avg_after[0]
        avg_change_5_to_10_after = avg_after[2] - avg_after[1]
        ax2.annotate(f'Δ = {avg_change_1_to_5_after:.3f} µS', xy=(3, avg_after[0] + avg_change_1_to_5_after/2 + y_offset), fontsize=12, ha='center')
        ax2.annotate(f'Δ = {avg_change_5_to_10_after:.3f} µS', xy=(7, avg_after[1] + avg_change_5_to_10_after/2 + y_offset), fontsize=12, ha='center')

        #sd_lines_after = [f"{tp}s: {sd:.3f} µS" for tp, sd in zip(time_points, std_after)]
        #sd_text_after = "Std (µS)\n" + "\n".join(sd_lines_after)
        #ax2.text(0.98, 0.95, sd_text_after, transform=ax2.transAxes, ha='right', va='top', fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

        print(f"\nConductance Change Analysis (in µS):")
        print(f"Original samples: {total_original}")
        print(f"Outliers removed: {cond_outliers}")
        print(f"BEFORE avg baseline (1s): {avg_before[0]:.3f} µS, AFTER avg baseline (1s): {avg_after[0]:.3f} µS")

        plt.tight_layout()

        main_plot_filename = 'conductance_before_after_plot_second_iteration_candidate_selection.png'
        plt.savefig(main_plot_filename, dpi=300, bbox_inches='tight')
        print(f"\nPlot saved as '{main_plot_filename}'")

        # --- EXTRA: save a plot containing ONLY the outlier traces ---
        try:
            out_indices = np.where(outlier_mask)[0]
            n_out = out_indices.size
            if n_out > 0:
                fig_o, ax_o = plt.subplots(1, 1, figsize=(8, 6))
                for i in out_indices:
                    vals = [
                        conductance_1s[i], conductance_2s[i], conductance_3s[i],
                        conductance_4s[i], conductance_5s[i], conductance_6s[i],
                        conductance_7s[i], conductance_8s[i], conductance_9s[i],
                        conductance_10s[i],
                    ]
                    ax_o.plot(time_points, vals, color=COLORS['conductance_sample'], alpha=0.7, linewidth=1.0)

                avg_out = [np.nanmean(conductance[out_indices]) for conductance in c_stack]
                std_out = [np.nanstd(conductance[out_indices]) for conductance in c_stack]
                #ax_o.plot(time_points, avg_out, color=COLORS['conductance_avg_trend'], linewidth=3, marker='o', label=f'Avg outliers (n={n_out})')
                #ax_o.set_title('Conductance — OUTLIERS only')
                ax_o.set_xlabel('Time (seconds)')
                ax_o.set_ylabel('Conductance (µS)')
                ax_o.set_xticks(time_points)
                ax_o.grid(True, alpha=0.3)
                #ax_o.legend(fontsize=FONT_SIZES['legend'])

                # annotate std box
                #sd_lines_o = [f"{tp}s: {sd:.3f} µS" for tp, sd in zip(time_points, std_out)]
                #sd_text_o = "Std (µS)\n" + "\n".join(sd_lines_o)
                #ax_o.text(0.98, 0.95, sd_text_o, transform=ax_o.transAxes, ha='right', va='top', fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

                out_fname = 'conductance_outliers_only_plot_second_iteration_candidate_selection.png'
                fig_o.tight_layout()
                fig_o.savefig(out_fname, dpi=300, bbox_inches='tight')
                plt.close(fig_o)
                print(f"Saved outliers-only figure: {out_fname} (n={n_out})")
            else:
                print("No outliers to plot in outliers-only figure")
        except Exception as e:
            print(f"Could not create outliers-only figure: {e}")

        # --- EXTRA 2: plot applied Voltage vs sample time for the outliers ---
        try:
            # assume columns 4 and 5 (1-based) => zero-based indices 3 and 4
            if data.shape[1] > 4:
                voltage_col = pd.to_numeric(data.iloc[:, 3], errors='coerce').to_numpy(dtype=float)
                time_col = pd.to_numeric(data.iloc[:, 4], errors='coerce').to_numpy(dtype=float)
                time_col = time_col * 1e3  # convert to microseconds

                volt_out = voltage_col[outlier_mask]
                time_out = time_col[outlier_mask]

                if volt_out.size > 0 and np.any(np.isfinite(time_out)):
                    fig_v, ax_v = plt.subplots(figsize=(7, 5))
                    # color by state if available
                    try:
                        state_all = data.iloc[:, 0].astype(str).str.strip().str.lower().to_numpy()
                        state_out_v = state_all[outlier_mask]
                        colors = ['tab:orange' if s == 'set' else 'tab:blue' if s == 'reset' else 'gray' for s in state_out_v]
                    except Exception:
                        colors = 'tab:gray'

                    ax_v.scatter(time_out, volt_out, c=colors, alpha=0.8, edgecolor='k')
                    ax_v.set_xlabel('Pulse width [µS]')
                    ax_v.set_ylabel('Voltage (V)')
                    #ax_v.set_title('Outliers: Applied voltage vs pulse width')
                    ax_v.grid(alpha=0.3)

                    # annotate each point with conductance_before (col10) / conductance_after (col12)
                    try:
                        out_idx = np.where(outlier_mask)[0]
                        # Remove any previously added text annotations on this axis to avoid
                        # duplicates or leftover values behind the desired labels.
                        for _t in list(ax_v.texts):
                            try:
                                _t.remove()
                            except Exception:
                                pass

                        if volt_out.size > 0:
                            yspan = np.nanmax(volt_out) - np.nanmin(volt_out)
                            yoff = 0.02 * yspan if np.isfinite(yspan) and yspan > 0 else 0.01
                        else:
                            yoff = 0.01

                        for k, idx in enumerate(out_idx):
                            x = time_out[k]
                            y = volt_out[k]
                            # read conductance_before (col 10 -> idx 9) and conductance_after (col 12 -> idx 11)
                            # convert from S to µS to match plotted conductance units
                            try:
                                cb_raw = pd.to_numeric(data.iloc[idx, 9], errors='coerce')
                                cb = float(cb_raw) * 1e6 if np.isfinite(cb_raw) else np.nan
                            except Exception:
                                cb = np.nan
                            try:
                                ca_raw = pd.to_numeric(data.iloc[idx, 11], errors='coerce')
                                ca = float(ca_raw) * 1e6 if np.isfinite(ca_raw) else np.nan
                            except Exception:
                                ca = np.nan
                            cb_s = f"{cb:.2f}" if np.isfinite(cb) else "NA"
                            ca_s = f"{ca:.2f}" if np.isfinite(ca) else "NA"
                            txt = f"{cb_s}/{ca_s}"
                            # Use an opaque white bbox and a higher z-order so the label fully
                            # covers any underlying plot content and sits on top.
                            ax_v.text(
                                x + 0.1,
                                y + yoff,
                                txt,
                                fontsize=8,
                                ha='left',
                                va='bottom',
                                bbox=dict(facecolor='white', alpha=1.0, edgecolor='none'),
                                zorder=5,
                                clip_on=True,
                            )
                    except Exception:
                        pass

                    fig_v.tight_layout()
                    v_fname = 'outliers_voltage_vs_time_second_iteration_candidate_selection.png'
                    fig_v.savefig(v_fname, dpi=300, bbox_inches='tight')
                    plt.close(fig_v)
                    print(f"Saved voltage vs time scatter for outliers: {v_fname} (n={volt_out.size})")

                # Additionally plot the applied voltage across the measurement times for each outlier
                if volt_out.size > 0:
                    fig_v2, ax_v2 = plt.subplots(figsize=(8, 6))
                    for idx in np.where(outlier_mask)[0]:
                        v = voltage_col[idx]
                        # plot horizontal line at voltage across the 1s/5s/10s measurement points
                        ax_v2.plot([1, 5, 10], [v, v, v], color=COLORS['conductance_sample'], alpha=0.6)

                    avg_v = np.nanmean(volt_out)
                    ax_v2.plot([1, 5, 10], [avg_v, avg_v, avg_v], color=COLORS['conductance_avg_trend'], linewidth=3, marker='o', label=f'Avg V (outliers)={avg_v:.3f}')
                    ax_v2.set_xlabel('Time (s)')
                    ax_v2.set_ylabel('Applied voltage')
                    ax_v2.set_title('Applied Voltage for OUTLIER samples (constant across measurement times)')
                    ax_v2.set_xticks([1, 5, 10])
                    ax_v2.grid(alpha=0.3)
                    ax_v2.legend(fontsize=FONT_SIZES['legend'])
                    fig_v2.tight_layout()
                    v_fname2 = 'outliers_voltage_over_measure_times_second_iteration_candidate_selection.png'
                    fig_v2.savefig(v_fname2, dpi=300, bbox_inches='tight')
                    plt.close(fig_v2)
                    print(f"Saved outliers voltage-over-measure-times plot: {v_fname2}")
            else:
                print("CSV does not contain columns 4/5 — skipping voltage/time outlier plots")
        except Exception as e:
            print(f"Could not create voltage/time outlier plots: {e}")

        #plt.show()

    except FileNotFoundError:
        print(f"ERROR: CSV file '{csv_file}' not found!")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        print("Please check your CSV file format and column indices")


def find_and_plot():
    csv_dir = 'data/d2d_original_data'
    filenames = ['train_samples_dev_1_46_1000_samples_low_ratio.csv', 'train_samples_dev_20_21_1000_samples_low_ratio.csv', 'train_samples_dev_45_40_1000_samples_low_ratio.csv', 'train_samples_dev_50_12_1000_samples_low_ratio.csv', 'train_samples_dev_57_27_1000_samples_low_ratio.csv',
                 'train_samples_dev_28_15_1000_samples_high_ratio.csv', 'train_samples_dev_32_22_1000_samples_high_ratio.csv', 'train_samples_dev_44_41_1000_samples_high_ratio.csv', 'train_samples_dev_49_56_1000_samples_high_ratio.csv', 'train_samples_dev_60_15_1000_samples_high_ratio.csv']
    data = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    if data:
        print(f"Found CSV files: {data}")
        for filename in filenames:
            csv_filename = os.path.join(csv_dir, filename)
            print(f"Using CSV file: {csv_filename}")
            plot_conductance_over_time(csv_filename)
    else:
        print(f"No CSV files found in directory '{csv_dir}'.")


if __name__ == "__main__":
    find_and_plot()
