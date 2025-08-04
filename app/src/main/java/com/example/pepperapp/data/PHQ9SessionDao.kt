package com.example.pepperapp.data

import androidx.room.*
import com.example.pepperapp.model.PHQ9Session
import kotlinx.coroutines.flow.Flow

@Dao
interface PHQ9SessionDao {
    @Query("SELECT * FROM phq9_sessions ORDER BY timestamp DESC")
    fun getAllSessions(): Flow<List<PHQ9Session>>

    @Query("SELECT * FROM phq9_sessions WHERE id = :id")
    suspend fun getSessionById(id: Long): PHQ9Session?

    @Insert
    suspend fun insertSession(session: PHQ9Session): Long

    @Delete
    suspend fun deleteSession(session: PHQ9Session)

    @Query("DELETE FROM phq9_sessions")
    suspend fun deleteAllSessions()
} 