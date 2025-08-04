package com.example.pepperapp.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.example.pepperapp.model.PHQ9Session
import com.example.pepperapp.model.UserProfile

@Database(
    entities = [UserProfile::class, PHQ9Session::class], 
    version = 10
)
@TypeConverters(Converters::class)
abstract class PepperDatabase : RoomDatabase() {

    abstract fun userProfileDao(): UserProfileDao
    abstract fun phq9SessionDao(): PHQ9SessionDao

    companion object {
        @Volatile
        private var INSTANCE: PepperDatabase? = null

        fun getDatabase(context: Context): PepperDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    PepperDatabase::class.java,
                    "pepper_database"
                )
                    .fallbackToDestructiveMigration()
                    .build()

                INSTANCE = instance
                instance
            }
        }
    }
}
