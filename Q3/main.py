from datetime import datetime
from datetime import timedelta

import csv
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import re

FOLDER_EXECUTIONS: str = "results"
FOLDER_IMAGES: str = "images"
FOLDER_DATABASE: str = "database"

FILE_LOGS: str = "logs.csv"
FILE_POWERS: str = "powers.csv"
FILE_TIMINGS: str = "timings.csv"
FILE_UTILIZATIONS: str = "utilizations.csv"

PATH_FILE: str = os.path.dirname(os.path.abspath(__file__))
PATH_DATABASE_LOGS: str = os.path.join(PATH_FILE, FOLDER_DATABASE, FILE_LOGS)
PATH_DATABASE_POWERS: str = os.path.join(PATH_FILE, FOLDER_DATABASE, FILE_POWERS)
PATH_DATABASE_TIMINGS: str = os.path.join(PATH_FILE, FOLDER_DATABASE, FILE_TIMINGS)
PATH_DATABASE_UTILIZATIONS: str = os.path.join(PATH_FILE, FOLDER_DATABASE, FILE_UTILIZATIONS)



def csv_create(headers: list, csv_path: str) -> None:
	"""
	Create a CSV file with the specified headers if it does not already exist.

	Args:
		headers (list): list of strings representing the column headers for the CSV file.
		csv_path (str): path where the CSV file will be created.
	"""
	if not os.path.exists(csv_path):
		with open(csv_path, mode='w') as file:
			writer = csv.writer(file)
			writer.writerow(headers)

def csv_append(row: list, csv_path: str) -> None:
	"""
	Appends a row of data to a CSV file.

	Args:
		row (list): row of data to append to the CSV file.
		csv_path (str): path to the CSV file.
	"""
	try:
		with open(csv_path, 'a') as file:
			writer = csv.writer(file)
			writer.writerow(row)
	except Exception as e:
		raise Exception("Error saving data: {}".format(str(e)))


def set_path(file: str, folder: str = FOLDER_DATABASE) -> str:
	"""
	Return a full file path by joining the base path, folder, and file name.

	Args:
		file (str): name of the file.
		folder (str, optional): name of the folder. Defaults to FOLDER_DATABASE.
	"""
	return os.path.join(PATH_FILE, folder, file)


def convert_duration(duration: str) -> int:
	"""
	Return converted duration value in seconds of string in the format "HH:MM:SS".

	Args:
		duration (str): duration string in the format "HH:MM:SS".
	"""
	h, m, s = map(int, duration.split(":"))

	return int(timedelta(hours=h, minutes=m, seconds=s).total_seconds())

def convert_mW(value: float) -> int:
	"""
	Return converted value from watts to milliwatts.
	Args:
		value (float): The value in watts to be converted.
	"""
	if np.isnan(value):
		return 0

	return int(value * 1000)

def extract_regex(path: str, patterns: dict, all_matches: bool = False) -> dict:
	"""
	Return a dictionary of extracted data from a file based on provided regex patterns.

	Args:
		path (str): file path to extract data.
		patterns (dict): labels and patterns for regex search.
		all_matches (bool, optional): If True, return all matches for each pattern.
									  If False, return only first match for each pattern.
	"""
	extracted_data: dict = {key: [] for key in patterns.keys()}

	with open(path, 'r', encoding='utf-8') as file:
		content = file.read()

		for label, pattern in patterns.items():
			matches: list = re.findall(pattern, content, flags=re.MULTILINE)

			if not matches:
				matches.append("NA")

			extracted_data[label] = matches if all_matches else matches[0]

	return extracted_data



def database_create() -> None:
	"""
	Creates CSV files for different database categories with specified headers.
	"""
	csv_files: dict = {
		set_path(PATH_DATABASE_LOGS): [
			"strategy_synthesis",
			"strategy_implementation",
			"datetime_execution",
			"duration_execution",
			"duration_synthesis",
			"duration_implementation"
		],
		set_path(PATH_DATABASE_POWERS): [
			"strategy_synthesis",
			"strategy_implementation",
			"power_total",
			"power_dynamic",
			"power_static",
			"power_clocks",
			"power_logic",
			"power_signals",
			"power_block_RAM",
			"power_IO",
			"power_PS7",
			"temperature_ambient_max",
			"temperature_junction",
			"confidence"
		],
		set_path(PATH_DATABASE_TIMINGS): [
			"strategy_synthesis",
			"strategy_implementation",
			"WNS",
			"TNS",
			"TNS_endpoints_failing",
			"TNS_endpoints_total",
			"WPWS",
			"TPWS",
			"TPWS_endpoints_failing",
			"TPWS_endpoints_total",
		],
		set_path(PATH_DATABASE_UTILIZATIONS): [
			"strategy_synthesis",
			"strategy_implementation",
			"LUT_logic",
			"LUT_memory",
			"slice_registers_FF",
			"block_RAM",
			"IOB",
			"BUFGCTRL",
		]
	}

	for path, headers in csv_files.items():
		csv_create(headers, path)

def database_update() -> None:
	"""
	Update all CSV dabase files.
	"""
	executions: list = os.listdir(os.path.join(PATH_FILE, FOLDER_EXECUTIONS))

	for execution in executions:
		folder_execution: str = os.path.join(PATH_FILE, FOLDER_EXECUTIONS, execution)
		synthesis, implementation = execution.split("__")

		update_logs(
			synthesis, implementation, os.path.join(folder_execution, FILE_LOGS)
		)

		update_powers(
			synthesis, implementation, os.path.join(folder_execution, FILE_POWERS)
		)

		update_timings(
			synthesis, implementation, os.path.join(folder_execution, FILE_TIMINGS)
		)

		update_utilizations(
			synthesis, implementation, os.path.join(folder_execution, FILE_UTILIZATIONS)
		)


def update_logs(
		synthesis: str, implementation: str, path: str, database: str = PATH_DATABASE_LOGS
	) -> None | int:
	"""
	Update 'logs.csv' database file with execution results.

	Args:
		synthesis (str): synthesis strategy used on execution.
		implementation (str): implementation used on execution.
		path (str): execution's 'log_run.csv' file path.
		database (str): databse's 'logs.csv' path. Default value is 'PATH_DATABASE_LOGS'.
	"""
	if not os.path.exists(path):
		print("invalid file")
		return -1

	execution_df = pd.read_csv(path, names=["datetime", "execution", "action", "state"])

	if not f"{synthesis}__{implementation}" == execution_df.execution.iloc[0]:
		print(
			f"incompatible file: {synthesis}__{implementation} != {execution_df.execution.iloc[0]}"
		)

		return -1

	# execution timing
	execution_start = datetime.strptime(execution_df.datetime.iloc[0], "%Y-%m-%d %H:%M:%S")
	execution_finish = datetime.strptime(execution_df.datetime.iloc[-1], "%Y-%m-%d %H:%M:%S")
	execution_duration = execution_finish - execution_start

	# synthesis timing
	synth_df = execution_df.query("action == 'run synthesis'")

	synth_start = datetime.strptime(synth_df.datetime.iloc[0], "%Y-%m-%d %H:%M:%S")
	synth_finish = datetime.strptime(synth_df.datetime.iloc[-1], "%Y-%m-%d %H:%M:%S")
	synth_duration = synth_finish - synth_start

	# implementation timing
	imple_df = execution_df.query("action == 'run implementation'")

	imple_start = datetime.strptime(imple_df.datetime.iloc[0], "%Y-%m-%d %H:%M:%S")
	imple_finish = datetime.strptime(imple_df.datetime.iloc[-1], "%Y-%m-%d %H:%M:%S")
	imple_duration = imple_finish - imple_start

	# create csv data row
	data_log: list = [
		synthesis,
		implementation,
		execution_start,
		execution_duration,
		synth_duration,
		imple_duration
	]

	csv_append(data_log, database)

def update_powers(
		synthesis: str, implementation: str, path: str, database: str = PATH_DATABASE_POWERS
	) -> None:
	"""
	Update CSV database of power and temperature metrics from a given file.

	Args:
		synthesis (str): synthesis method.
		implementation (str): implementation method.
		path (str): file path to extract data.
		database (str, optional): CSV database file path where data will be logged.
	"""
	if not os.path.exists(path):
		return "invalid file"

	patterns: dict = {
		"power_total": r"Total On-Chip Power \(W\)\s+\|\s+([\d.]+)",
		"power_dynamic": r"Dynamic \(W\)\s+\|\s+([\d.]+)",
		"power_static": r"Device Static \(W\)\s+\|\s+([\d.]+)",
		"power_clocks": r"Clocks\s+\|\s+([\d.]+)",
		"power_logic": r"Slice Logic\s+\|\s+([\d.]+)",
		"power_signals": r"Signals\s+\|\s+([\d.]+)",
		"power_block_RAM": r"Block RAM\s+\|\s+([\d.]+)",
		"power_IO": r"I/O\s+\|\s+<?([\d.]+)",
		"power_PS7": r"PS7\s+\|\s+([\d.]+)",
		"temperature_ambient_max": r"Max Ambient \(C\)\s+\|\s+([\d.]+)",
		"temperature_junction": r"Junction Temperature \(C\)\s+\|\s+([\d.]+)",
		"confidence": r"Confidence Level\s+\|\s+(\w+)",
	}

	results: dict = extract_regex(path, patterns)

	# create csv data row
	data_log: list = [
		synthesis,
		implementation,
		results["power_total"],
		results["power_dynamic"],
		results["power_static"],
		results["power_clocks"],
		results["power_logic"],
		results["power_signals"],
		results["power_block_RAM"],
		results["power_IO"],
		results["power_PS7"],
		results["temperature_ambient_max"],
		results["temperature_junction"],
		results["confidence"],
	]

	csv_append(data_log, database)

def update_timings(
		synthesis: str, implementation: str, path: str, database: str = PATH_DATABASE_TIMINGS
	) -> None:
	"""
	Update CSV database of timing metrics from a given file.

	Args:
		synthesis (str): synthesis method.
		implementation (str): implementation method.
		path (str): file path to extract data.
		database (str, optional): CSV database file path where data will be logged.
	"""
	if not os.path.exists(path):
		return "invalid file"
	
	pattern: dict = {"timing": r"^\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)"}

	results: dict = extract_regex(path, pattern, all_matches=True)

	# create csv data row
	data_log: list = [
		synthesis,
		implementation,
		results["timing"][0][0],
		results["timing"][0][1],
		results["timing"][0][2],
		results["timing"][0][3],
		results["timing"][0][8],
		results["timing"][0][9],
		results["timing"][0][10],
		results["timing"][0][11],
	]

	csv_append(data_log, database)

def update_utilizations(
		synthesis: str, implementation: str, path: str, database: str = PATH_DATABASE_UTILIZATIONS
	) -> None:
	"""
	Update CSV database of utilization metrics from a given file.

	Args:
		synthesis (str): synthesis method.
		implementation (str): implementation method.
		path (str): file path to extract data.
		database (str, optional): CSV database file path where data will be logged.
	"""
	if not os.path.exists(path):
		return "invalid file"

	patterns: dict = {
		"LUT_logic": r"LUT as Logic\s+\|\s+[\d.]+\s+\|\s+[\d]+\s+\|\s+[\d]+\s+\|\s+([\d.]+)",
		"LUT_memory": r"LUT as Memory\s+\|\s+[\d.]+\s+\|\s+[\d]+\s+\|\s+[\d]+\s+\|\s+([\d.]+)",
		"slice_registers_FF": r"Register as Flip Flop\s+\|\s+[\d.]+\s+\|\s+[\d]+\s+\|\s+[\d]+\s+\|\s+([\d.]+)",
		"block_RAM": r"Block RAM Tile\s+\|\s+[\d.]+\s+\|\s+[\d]+\s+\|\s+[\d]+\s+\|\s+([\d.]+)",
		"IOB": r"Bonded IOB\s+\|\s+[\d.]+\s+\|\s+[\d]+\s+\|\s+[\d]+\s+\|\s+([\d.]+)",
		"BUFGCTRL": r"BUFGCTRL\s+\|\s+[\d.]+\s+\|\s+[\d]+\s+\|\s+[\d]+\s+\|\s+([\d.]+)",
	}

	results: dict = extract_regex(path, patterns)

	# create csv data row
	data_log: list = [
		synthesis,
		implementation,
		results["LUT_logic"],
		results["LUT_memory"],
		results["slice_registers_FF"],
		results["block_RAM"],
		results["IOB"],
		results["BUFGCTRL"],
	]
	
	csv_append(data_log, database)



def plot_grid(
		grid_data: pd.DataFrame,
		title: str,
		legend: str,
		cmap: str = 'inferno',
		vmin: int = 0,
		vmax: int = 0,
		save: bool = True,
		show: bool = False,
	) -> None:
	"""
	Creates a Grid Plot with a Pandas DataFrame grid data.

	Args:
		grid_data (pd.DataFrame): data to be plotted in the grid.
		title (str): title of the plot.
		legend (str): legend of the color bar.
		cmap (str, optional): colormap to be used for the plot. Default is 'inferno'.
		vmin (int, optional): minimum data value that corresponds to the colormap. Default is 0.
		vmax (int, optional): maximum data value that corresponds to the colormap. Default is 0.
		save (bool, optional): If True, saves the plot as a PNG file. Default is True.
		show (bool, optional): If True, displays the plot. Default is False.
	"""
	plt.figure(figsize=(12, 8), dpi=150)

	if vmin == vmax:
		# automatic minimum and maximum
		plt.imshow(grid_data, cmap=f'{cmap}', origin='lower')
	else:
		plt.imshow(grid_data, cmap=f'{cmap}', origin='lower', vmin=vmin, vmax=vmax)

	plt.colorbar(label=f'{legend}', shrink=1.0, pad=0.01)
	plt.xlabel('Strategy Implementation')
	plt.ylabel('Strategy Synthesis')

	for i in range(len(grid_data.index)):
		for j in range(len(grid_data.columns)):
			plt.text(
				j, i, f'{grid_data.iloc[i, j]}', ha='center', va='center', color='w', fontsize=16
			)

	plt.title(f'{title}')
	plt.xticks(
		ticks=range(len(grid_data.columns)),
		labels=grid_data.columns,
		fontsize=7.5
	)
	plt.yticks(
		ticks=range(len(grid_data.index)),
		labels=grid_data.index,
		fontsize=7.5,
		rotation=90,
		va='center'
	)
	plt.tight_layout()

	if save:
		plt.savefig(f'{FOLDER_IMAGES}/{title}.png', dpi=300, bbox_inches='tight')

	if show:
		plt.show()

def plot_bars(synthesis: str, save: bool = True, show: bool = False) -> None:
	title = f"utilization_{synthesis}"

	df = pd.read_csv(PATH_DATABASE_UTILIZATIONS)
	df_execution = df.query(f"strategy_synthesis == '{synthesis}'")

	bar_width = 0.15
	fig, ax = plt.subplots(figsize=(12, 8), dpi=300)

	variables = ["LUT_logic", "LUT_memory", "slice_registers_FF", "block_RAM", "IOB", "BUFGCTRL"]

	num_bars = len(variables)
	bar_positions = range(len(df_execution))

	for i, var in enumerate(variables):
		positions = [p + i * bar_width for p in bar_positions]
		values = df_execution[var].values

		bars = ax.bar(
			positions,
			values,
			width=bar_width,
			label=var,
			edgecolor='black'
		)

		for bar in bars:
			height = bar.get_height()
			ax.text(
				bar.get_x() + bar.get_width() / 2,
				height + 1,
				f"{height:.2f}",
				ha='center',
				va='bottom',
				fontsize=6
			)

	ax.set_xlabel('Strategy Implementation')
	ax.set_xticks([p + bar_width * (num_bars / 2 - 0.5) for p in bar_positions])
	ax.set_xticklabels(df_execution['strategy_implementation'].values, fontsize=8)

	ax.set_ylim(0, 100)
	ax.set_ylabel('Percentage [%]')
	ax.set_yticks(range(0, 101, 10))
	ax.set_yticklabels([str(i) for i in range(0, 101, 10)])

	ax.set_title(f'Hardware Utilization of Strategy Synthesis: {synthesis}')
	ax.grid(True, axis='y', linestyle='--', alpha=0.7)
	ax.legend(loc='upper right')

	plt.tight_layout()

	if save:
		plt.savefig(f'{FOLDER_IMAGES}/{title}.png', dpi=300, bbox_inches='tight')

	if show:
		plt.show()


def plot_duration(phase: str, save: bool = True, show: bool = False) -> None:
	"""
	Plots the duration of a specified phase (execution, synthesis, or implementation) from an
	execution.

	Args:
		phase (str): phase of execution to plot: 'execution', 'synthesis', or 'implementation'.
		save (bool, optional): If True, saves the plot as a PNG file. Defaults to True.
		show (bool, optional): If True, displays the plot. Defaults to False.
	"""
	df = pd.read_csv(PATH_DATABASE_LOGS)
	df[f"duration_{phase}_s"] = df[f"duration_{phase}"].apply(convert_duration)

	grid_data = df.pivot(
		index='strategy_synthesis',
		columns='strategy_implementation',
		values=f'duration_{phase}_s'
	)

	plot_grid(
		grid_data,
		f'duration_{phase}', 'Execution Duration [s]',
		vmin=100, vmax=400, save=save, show=show)

def plot_durations() -> None:
	durations = ['execution', 'synthesis', 'implementation']

	for duration in durations:
		plot_duration(duration)


def plot_power(type: str, save: bool = True, show: bool = False) -> None:
	df = pd.read_csv(PATH_DATABASE_POWERS)

	for power in ["power_total", "power_dynamic", "power_static", "power_clocks", "power_logic", "power_signals", "power_block_RAM", "power_IO", "power_PS7"]:
		df[f'{power}_mW'] = df[f'{power}'].apply(convert_mW)

	grid_data = df.pivot(
		index='strategy_synthesis',
		columns='strategy_implementation',
		values=f'{type}_mW'
	)

	plot_grid(grid_data, f'{type}_mW', 'Power Consumption [mW]', cmap='ocean', vmin=0, vmax=2000, save=save, show=show)

def plot_powers() -> None:
	types = ['power_total', 'power_dynamic', 'power_static']

	for type in types:
		plot_power(type)

def plot_powers_details(synthesis: str, implementation: str, save: bool = True, show: bool = False) -> None:
	title = f"power_{synthesis}_{implementation}"

	df = pd.read_csv(PATH_DATABASE_POWERS)

	df_execution = df.query(f"strategy_synthesis == '{synthesis}' & strategy_implementation == '{implementation}'")
	df_execution.fillna(0, inplace=True)

	power_dynamic = df_execution['power_dynamic'].iloc[0]
	power_static = df_execution['power_static'].iloc[0]
	power_total = power_dynamic + power_static

	power_clocks = df_execution['power_clocks'].iloc[0]
	power_logic = df_execution['power_logic'].iloc[0]
	power_signals = df_execution['power_signals'].iloc[0]
	power_block_RAM = df_execution['power_block_RAM'].iloc[0]
	power_IO = df_execution['power_IO'].iloc[0]
	power_PS7 = df_execution['power_PS7'].iloc[0]

	power_dynamic_details = [
		power_static / power_total,
		power_clocks / power_total,
		power_logic / power_total,
		power_signals / power_total,
		power_block_RAM / power_total,
		power_IO / power_total,
		power_PS7 / power_total,
	]

	inner_labels = ["", "Clocks", "Logic", "Signals", "Block RAM", "IO", "PS7"]
	outer_labels = ["Static", "Dynamic"]
	power_dynamic_static = [power_static, power_dynamic]

	tab10 = plt.cm.tab10
	tab20c = plt.cm.tab20c
	outer_colors = [tab20c(8), tab20c(12)]
	inner_colors = ['w', tab10(0), tab10(1), tab10(3), tab10(5), tab10(6), tab10(7)]

	fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
	plt.title(title, fontsize=14)

	wedges_outer, texts_outer= ax.pie(
		power_dynamic_static,
		radius=1 - 0.325,
		colors=outer_colors,
		wedgeprops=dict(width=0.3, edgecolor='w'),
		pctdistance=0.85
	)

	wedges_inner, texts_inner = ax.pie(
		power_dynamic_details,
		radius=1,
		colors=inner_colors,
		wedgeprops=dict(width=0.3, edgecolor='w'),
		pctdistance=0.85
	)

	legend_labels = []
	legend_labels.append(f"{power_static:.3f} W [{power_static/power_total*100:05.2f}%], Static")
	legend_labels.append(f"{power_dynamic:.3f} W [{power_dynamic/power_total*100:05.2f}%], Dynamic")

	for i, detail in enumerate(power_dynamic_details):
		legend_labels.append(f"{detail * power_total:.3f} W [{detail*100:05.2f}%], {inner_labels[i]}")

	legend_labels[2] = ""

	ax.legend(
		wedges_outer + wedges_inner,
		legend_labels,
		loc="center left",
		bbox_to_anchor=(1, 0.5),
		fontsize=12,
		frameon=False
	)

	ax.text(
		1.30,
		0.75,
		f"Confidence Level: {df_execution['confidence'].iloc[0]}\n\n" +
		f"Total Power Consumption: {power_total:.3f} W\n\n" +
		f"Temperature Ambient: {df_execution['temperature_ambient_max'].iloc[0]} C\n" +
		f"Temperature Junction: {df_execution['temperature_junction'].iloc[0]} C",
		fontsize=12,
		ha='left',
		va='center',
	)

	ax.set(aspect="equal")
	plt.tight_layout()

	if save:
		plt.savefig(f'{FOLDER_IMAGES}/{title}.png', dpi=300, bbox_inches='tight')

	if show:
		plt.show()


def plot_timings(value: str, save: bool = True, show: bool = False) -> None:
	df = pd.read_csv(PATH_DATABASE_TIMINGS)

	grid_data = df.pivot(
		index = 'strategy_synthesis',
		columns = 'strategy_implementation',
		values = f'{value}'
	)

	plot_grid(
		grid_data,
		f'timing_{value}',
		'Execution Duration [s]',
		cmap = 'seismic',
		save = save,
		show = show
	)



def main():
	# database_create()

	# database_update()

	plot_durations()

	plot_powers()

	syntheses = [
		"Flow_AreaOptimized_high",
		"Flow_PerfOptimized_high",
		"Flow_PerfThresholdCarry",
		"Flow_RuntimeOptimized",
		"Vivado Synthesis Defaults"
	]
	implementations = [
		"Area_Explore",
		"Congestion_SSI_SpreadLogic_high",
		"Flow_Quick",
		"Performance_Explore",
		"Power_ExploreArea",
		"Vivado Implementation Defaults"
	]
	for synthesis in syntheses:
		for implementation in implementations:
			plot_powers_details(synthesis, implementation, save=True, show=False)

	for synthesis in syntheses:
		plot_bars(synthesis)

	plot_timings('WNS')



if __name__ == "__main__":
	main()
