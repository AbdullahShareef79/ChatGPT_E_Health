package com.example.pepperapp.config

enum class RobotMode {
    PEPPER_REAL,
    SIMULATION
}

object RobotConfig {
    // Set to SIMULATION to run without Pepper robot
    // Set to PEPPER_REAL when running on actual Pepper hardware
    var currentRobotMode: RobotMode = RobotMode.SIMULATION
    
    fun isSimulationMode(): Boolean = currentRobotMode == RobotMode.SIMULATION
    
    fun isPepperMode(): Boolean = currentRobotMode == RobotMode.PEPPER_REAL
}

