##########################################################################
##
## @file        : run.tcl
## @time        : 2024/12/11 13:29:00
## @author      : Guilherme NUNES TROFINO
## @version     : 0.0.1
## @contact     : guitrofino@gmail.com
## @license     : Copyright © 2007 Free Software Foundation, Inc.
## @description : execute multiple 3x3 NoC configurations in Vivado 2019.1 and save results.
##
##########################################################################




## helper functions
##########################################################################

# copy all files from source to destination folder
proc copy_all_files {folder_source folder_destination} {
    # create destination folder
    file mkdir $folder_destination

    # list of all files in source folder
    set files [glob -nocomplain "$folder_source/*"]

    # Loop through each file in source and copy to destination
    foreach file $files {
        set file_name [file tail $file]
        file copy -force $file "$folder_destination/$file_name"
    }
}

# log a message with a datetime
proc log_message {log_file message} {
    set datetime [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
    set file [open $log_file "a"]

    puts $file "$datetime,$message"

    close $file
}




## main function
##########################################################################

# run line below on a Vivado 2019.1 Tcl Shell
#   vivado -mode batch -source run.tcl

# define execution parameters
set execution_complete 1

set execution_open_project 0
set execution_run_synthesis 0
set execution_run_implementation 0

# define global variables
set cores_CPU 14

set name_project "Question3"
set name_top_module "design_1_wrapper"
set name_synthesis "synth_1"
set name_implementation "impl_1"

# define execution constants
set name_file "run"
set dir_results "./results"
set message_prefix "\n\n\[TCL\] INFO: $name_file\t"
set message_sulfix "\n==================================================\n\n\n\n"
file mkdir $dir_results

# define execution optimizations. first value is Vivado's default.
set strategies_synthesis {
    "Vivado Synthesis Defaults"
    "Flow_AreaOptimized_high"
    "Flow_PerfOptimized_high"
    "Flow_PerfThresholdCarry"
    "Flow_RuntimeOptimized"
}
set strategies_implementation {
    "Vivado Implementation Defaults"
    "Area_Explore"
    "Congestion_SSI_SpreadLogic_high"
    "Flow_Quick"
    "Performance_Explore"
    "Power_ExploreArea"
}


# execution variations
foreach strategy_synthesis $strategies_synthesis {
    foreach strategy_implementation $strategies_implementation {
        set name_execution "${strategy_synthesis}__${strategy_implementation}"

        set dir_execution "$dir_results/$name_execution"
        set file_log "$dir_execution/log_$name_file.csv"

        file mkdir $dir_execution

        log_message $file_log "$name_execution,execution,start"


        # initialize vivado project
        puts stdout "$message_prefix$name_execution workflow$message_sulfix"

        log_message $file_log "$name_execution,open project,start"
        if {$execution_complete || $execution_open_project} {
            open_project "$name_project.xpr"
        }
        log_message $file_log "$name_execution,open project,finish"


        # run synthesis
        puts stdout "$message_prefix$name_execution synthesis$message_sulfix"

        log_message $file_log "$name_execution,run synthesis,start"
        if {$execution_complete || $execution_run_synthesis} {
            set_property strategy ${strategy_synthesis} [get_runs $name_synthesis]

            reset_run $name_synthesis
            launch_runs $name_synthesis -jobs $cores_CPU
            wait_on_run $name_synthesis
        }
        log_message $file_log "$name_execution,run synthesis,finish"


        # run implementation
        puts stdout "$message_prefix$name_execution implementation$message_sulfix"

        log_message $file_log "$name_execution,run implementation,start"
        if {$execution_complete || $execution_run_implementation} {
            set_property strategy ${strategy_implementation} [get_runs $name_implementation]

            reset_run $name_implementation
            launch_runs $name_implementation -to_step write_bitstream -jobs $cores_CPU
            wait_on_run $name_implementation

            set path_report_utilization "./$name_project.runs/$name_implementation/${name_top_module}_utilization_placed.rpt"
            set path_report_timing "./$name_project.runs/$name_implementation/${name_top_module}_timing_summary_routed.rpt"
            set path_report_power "./$name_project.runs/$name_implementation/${name_top_module}_power_routed.rpt"
            set path_bitstream "./$name_project.runs/$name_implementation/${name_top_module}.bit"
            set path_exported_hardware "./$name_project.runs/$name_implementation/${name_top_module}.sysdef"

            file copy -force "$path_report_power" "$dir_execution/report_power.txt"
            file copy -force "$path_report_utilization" "$dir_execution/report_utilization.txt"
            file copy -force "$path_report_timing" "$dir_execution/report_timing.txt"
            file copy -force "$path_report_timing" "$dir_execution/bitstream.bit"
            file copy -force "$path_exported_hardware" "$dir_execution/exported_hardware.hdf"
        }
        log_message $file_log "$name_execution,run implementation,finish"


        # close project
        log_message $file_log "$name_execution,execution,finish"
        close_project
    }
}

exit
