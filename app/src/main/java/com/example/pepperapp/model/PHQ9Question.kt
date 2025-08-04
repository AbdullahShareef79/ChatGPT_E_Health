package com.example.pepperapp.model

data class PHQ9Question(
    val id: Int,
    val question: String,
    val options: List<String>,
    val scores: List<Int>
) {
    companion object {
        fun getPHQ9Questions(): List<PHQ9Question> = listOf(
            PHQ9Question(
                1,
                "Over the last 2 weeks, how often have you had little interest or pleasure in doing things?",
                listOf("Not at all", "Several days", "More than half the days", "Nearly every day"),
                listOf(0, 1, 2, 3)
            ),
            PHQ9Question(
                2,
                "Over the last 2 weeks, how often have you felt down, depressed, or hopeless?",
                listOf("Not at all", "Several days", "More than half the days", "Nearly every day"),
                listOf(0, 1, 2, 3)
            ),
            PHQ9Question(
                3,
                "Over the last 2 weeks, how often have you had trouble falling or staying asleep, or sleeping too much?",
                listOf("Not at all", "Several days", "More than half the days", "Nearly every day"),
                listOf(0, 1, 2, 3)
            ),
            PHQ9Question(
                4,
                "Over the last 2 weeks, how often have you felt tired or had little energy?",
                listOf("Not at all", "Several days", "More than half the days", "Nearly every day"),
                listOf(0, 1, 2, 3)
            ),
            PHQ9Question(
                5,
                "Over the last 2 weeks, how often have you had poor appetite or overeating?",
                listOf("Not at all", "Several days", "More than half the days", "Nearly every day"),
                listOf(0, 1, 2, 3)
            ),
            PHQ9Question(
                6,
                "Over the last 2 weeks, how often have you felt bad about yourself, or that you are a failure, or have let yourself or your family down?",
                listOf("Not at all", "Several days", "More than half the days", "Nearly every day"),
                listOf(0, 1, 2, 3)
            ),
            PHQ9Question(
                7,
                "Over the last 2 weeks, how often have you had trouble concentrating on things, such as reading the newspaper or watching television?",
                listOf("Not at all", "Several days", "More than half the days", "Nearly every day"),
                listOf(0, 1, 2, 3)
            ),
            PHQ9Question(
                8,
                "Over the last 2 weeks, how often have you been moving or speaking slowly enough that other people could have noticed?",
                listOf("Not at all", "Several days", "More than half the days", "Nearly every day"),
                listOf(0, 1, 2, 3)
            ),
            PHQ9Question(
                9,
                "Over the last 2 weeks, how often have you had thoughts that you would be better off dead or of hurting yourself in some way?",
                listOf("Not at all", "Several days", "More than half the days", "Nearly every day"),
                listOf(0, 1, 2, 3)
            )
        )
    }
} 