package com.example.pepperapp.ui.Fragments

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.MediaRecorder
import android.os.Bundle
import android.util.Log
import android.view.*
import android.view.inputmethod.InputMethodManager
import android.widget.*
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.aldebaran.qi.sdk.QiContext
import com.aldebaran.qi.sdk.QiSDK
import com.aldebaran.qi.sdk.RobotLifecycleCallbacks
import com.aldebaran.qi.sdk.builder.ListenBuilder
import com.aldebaran.qi.sdk.builder.SayBuilder
import com.aldebaran.qi.sdk.`object`.locale.Language
import com.aldebaran.qi.sdk.`object`.locale.Region
import com.aldebaran.qi.sdk.`object`.locale.Locale as QiLocale
import com.aldebaran.qi.sdk.`object`.conversation.ListenResult
import com.example.pepperapp.R
import com.example.pepperapp.data.PepperDatabase
import com.example.pepperapp.model.PHQ9Question
import com.example.pepperapp.model.PHQ9Session
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class ChatFragment : Fragment(), RobotLifecycleCallbacks {

    companion object {
        private const val TAG = "PHQ9ChatFragment"
        private const val RECORD_PERMISSION = Manifest.permission.RECORD_AUDIO
        private const val REQ_CODE_RECORD = 1001
    }

    private var qiContext: QiContext? = null
    private var greeted = false

    // PHQ-9 Screening State
    private var currentQuestionIndex = 0
    private val responses = mutableListOf<Int>()
    private val questions = PHQ9Question.getPHQ9Questions()
    private var isScreeningActive = false

    // OpenAI Configuration
    private val apiKey = "YOUR_OPENAI_API_KEY_HERE" // Replace with your actual OpenAI API key
    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    // UI Components
    private lateinit var messageContainer: LinearLayout
    private lateinit var scrollView: ScrollView
    private lateinit var progressText: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var questionEditText: EditText
    private lateinit var sendButton: Button
    private lateinit var micButton: ImageButton

    // Database
    private lateinit var database: PepperDatabase

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        val view = inflater.inflate(R.layout.fragment_chat, container, false)
        QiSDK.register(requireActivity(), this)

        // Initialize database
        database = PepperDatabase.getDatabase(requireContext())

        // Initialize UI components
        messageContainer = view.findViewById(R.id.messageContainer)
        scrollView = view.findViewById(R.id.scrollView)
        progressText = view.findViewById(R.id.progressText)
        progressBar = view.findViewById(R.id.progressBar)
        questionEditText = view.findViewById(R.id.editTextQuestion)
        sendButton = view.findViewById(R.id.buttonSendQuestion)
        micButton = view.findViewById(R.id.buttonMic)

        // Set up UI
        setupUI()
        
        return view
    }

    private fun setupUI() {
        questionEditText.post {
            questionEditText.requestFocus()
            showKeyboard()
        }

        sendButton.setOnClickListener {
            val text = questionEditText.text.toString().trim()
            if (text.isNotEmpty()) {
                if (isScreeningActive) {
                    handleScreeningResponse(text)
                } else {
                    handleUserInput(text)
                }
            } else {
                Toast.makeText(requireContext(),
                    "Please enter a response.", Toast.LENGTH_SHORT).show()
            }
        }

        micButton.setOnClickListener {
            if (isScreeningActive) {
                startVoiceRecognition()
            } else {
                Toast.makeText(requireContext(),
                    "Please start the health screening first.", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun startPHQ9Screening() {
        isScreeningActive = true
        currentQuestionIndex = 0
        responses.clear()
        
        // Show progress UI
        progressText.visibility = View.VISIBLE
        progressBar.visibility = View.VISIBLE
        progressBar.max = questions.size
        
        // Add welcome message
        addMessageBubble(
            "I will ask you a few questions to check how you've been feeling recently. " +
            "This is not a diagnosis, but it helps you understand your emotions better. " +
            "Please answer honestly based on the last 2 weeks.",
            isRobot = true
        )
        
        // Start with first question
        askCurrentQuestion()
    }

    private fun askCurrentQuestion() {
        if (currentQuestionIndex >= questions.size) {
            completeScreening()
            return
        }

        val question = questions[currentQuestionIndex]
        val questionText = "Question ${currentQuestionIndex + 1}: ${question.question}"
        
        addMessageBubble(questionText, isRobot = true)
        speak(questionText)
        
        // Update progress
        progressText.text = "Question ${currentQuestionIndex + 1} of ${questions.size}"
        progressBar.progress = currentQuestionIndex + 1
    }

    private fun handleScreeningResponse(response: String) {
        questionEditText.setText("")
        hideKeyboard()
        
        addMessageBubble(response, isRobot = false)
        
        // Parse response and get score
        val score = parseResponseToScore(response, currentQuestionIndex)
        responses.add(score)
        
        // Move to next question
        currentQuestionIndex++
        askCurrentQuestion()
    }

    private fun parseResponseToScore(response: String, questionIndex: Int): Int {
        val question = questions[questionIndex]
        val responseLower = response.lowercase()
        
        return when {
            responseLower.contains("not at all") || responseLower.contains("never") -> 0
            responseLower.contains("several days") || responseLower.contains("sometimes") -> 1
            responseLower.contains("more than half") || responseLower.contains("often") -> 2
            responseLower.contains("nearly every day") || responseLower.contains("always") -> 3
            else -> {
                // Try to match with options
                question.options.forEachIndexed { index, option ->
                    if (responseLower.contains(option.lowercase())) {
                        return question.scores[index]
                    }
                }
                1 // Default to "several days" if unclear
            }
        }
    }

    private fun completeScreening() {
        val totalScore = responses.sum()
        val severity = getSeverityLevel(totalScore)
        
        // Generate summary with OpenAI
        lifecycleScope.launch {
            val summary = generateSummary(totalScore, severity, responses)
            
            withContext(Dispatchers.Main) {
                addMessageBubble(summary, isRobot = true)
                speak(summary)
                
                // Save session to database
                saveSession(totalScore, severity, summary)
                
                // Reset UI
                isScreeningActive = false
                progressText.visibility = View.GONE
                progressBar.visibility = View.GONE
            }
        }
    }

    private fun getSeverityLevel(score: Int): String {
        return when {
            score <= 4 -> "minimal"
            score <= 9 -> "mild"
            score <= 14 -> "moderate"
            score <= 19 -> "moderately_severe"
            else -> "severe"
        }
    }

    private suspend fun generateSummary(
        totalScore: Int, 
        severity: String, 
        responses: List<Int>
    ): String = withContext(Dispatchers.IO) {
        val severityText = when (severity) {
            "minimal" -> "minimal symptoms"
            "mild" -> "mild symptoms"
            "moderate" -> "moderate symptoms"
            "moderately_severe" -> "moderately severe symptoms"
            "severe" -> "severe symptoms"
            else -> "some symptoms"
        }

        val prompt = """
            You are Pepper, a friendly robot conducting a mental health screening. 
            The person's total PHQ-9 score is $totalScore, which indicates $severityText of depression.
            
            Please provide a gentle, supportive, and empathetic response that:
            1. Acknowledges their participation
            2. Provides context about what the score means (without being clinical)
            3. Offers encouragement and support
            4. Reminds them this is not a diagnosis
            5. Suggests talking to a healthcare provider if they're concerned
            6. Maintains a warm, caring tone
            
            Keep the response conversational and under 3 sentences.
        """.trimIndent()

        try {
            val payload = JSONObject().apply {
                put("model", "gpt-4o-mini")
                put("messages", JSONArray().apply {
                    put(JSONObject().apply {
                        put("role", "system")
                        put("content", prompt)
                    })
                })
            }

            val body = payload.toString().toRequestBody("application/json".toMediaType())
            val request = Request.Builder()
                .url("https://api.openai.com/v1/chat/completions")
                .addHeader("Authorization", "Bearer $apiKey")
                .post(body)
                .build()

            client.newCall(request).execute().use { resp ->
                if (!resp.isSuccessful) {
                    return@withContext "Thank you for completing the screening. Your responses help us understand how you've been feeling. Remember, this is just a tool to help you reflect on your emotions. If you have concerns, please talk to a healthcare provider."
                }
                
                val text = resp.body?.string().orEmpty()
                val choices = JSONObject(text).getJSONArray("choices")
                val content = choices.getJSONObject(0)
                    .getJSONObject("message")
                    .optString("content", "").trim()
                
                if (content.isNotEmpty()) content else {
                    "Thank you for completing the screening. Your responses help us understand how you've been feeling. Remember, this is just a tool to help you reflect on your emotions. If you have concerns, please talk to a healthcare provider."
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error generating summary", e)
            "Thank you for completing the screening. Your responses help us understand how you've been feeling. Remember, this is just a tool to help you reflect on your emotions. If you have concerns, please talk to a healthcare provider."
        }
    }

    private fun saveSession(totalScore: Int, severity: String, summary: String) {
        lifecycleScope.launch {
            try {
                val session = PHQ9Session(
                    timestamp = System.currentTimeMillis(),
                    responses = responses.toList(),
                    totalScore = totalScore,
                    severity = severity,
                    gptSummary = summary
                )
                database.phq9SessionDao().insertSession(session)
                Log.d(TAG, "PHQ-9 session saved successfully")
            } catch (e: Exception) {
                Log.e(TAG, "Error saving PHQ-9 session", e)
            }
        }
    }

    private fun startVoiceRecognition() {
        val ctx = qiContext ?: return
        
        lifecycleScope.launch(Dispatchers.IO) {
            try {
                val listen = ListenBuilder.with(ctx)
                    .withLocale(QiLocale(Language.ENGLISH, Region.UNITED_STATES))
                    .build()
                
                val result = listen.async().run()
                val text = result.text
                
                withContext(Dispatchers.Main) {
                    questionEditText.setText(text)
                    questionEditText.setSelection(text.length)
                    handleScreeningResponse(text)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Voice recognition error", e)
                withContext(Dispatchers.Main) {
                    Toast.makeText(requireContext(), 
                        "Could not understand. Please type your response.", 
                        Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun handleUserInput(text: String) {
        questionEditText.setText("")
        hideKeyboard()
        addMessageBubble(text, isRobot = false)

        // Start PHQ-9 screening if user wants to
        if (text.lowercase().contains("health") || 
            text.lowercase().contains("screening") ||
            text.lowercase().contains("check") ||
            text.lowercase().contains("feeling")) {
            startPHQ9Screening()
        } else {
            addMessageBubble(
                "I'm here to help with a health screening. Would you like to start? " +
                "Just say 'yes' or type 'start screening' to begin.",
                isRobot = true
            )
            speak("I'm here to help with a health screening. Would you like to start?")
        }
    }

    private fun addMessageBubble(text: String, isRobot: Boolean): TextView {
        val bubble = TextView(requireContext()).apply {
            this.text = text
            setPadding(16, 12, 16, 12)
            setBackgroundResource(
                if (isRobot) R.drawable.bubble_robot else R.drawable.bubble_child
            )
            setTextColor(android.graphics.Color.WHITE)
        }
        val params = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ).apply {
            setMargins(0, 8, 0, 8)
            gravity = if (isRobot) Gravity.START else Gravity.END
        }
        bubble.layoutParams = params
        messageContainer.addView(bubble)
        scrollView.post { scrollView.fullScroll(View.FOCUS_DOWN) }
        return bubble
    }

    private fun speak(text: String, onDone: (() -> Unit)? = null) {
        val ctx = qiContext ?: run { onDone?.invoke(); return }
        lifecycleScope.launch(Dispatchers.IO) {
            val say = SayBuilder.with(ctx)
                .withText(text)
                .withLocale(QiLocale(Language.ENGLISH, Region.UNITED_STATES))
                .build()
            say.async().run().thenConsume { onDone?.invoke() }
        }
    }

    private fun hideKeyboard() {
        val imm = requireContext()
            .getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        imm.hideSoftInputFromWindow(questionEditText.windowToken, 0)
    }

    private fun showKeyboard() {
        val imm = requireContext()
            .getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        imm.showSoftInput(questionEditText, InputMethodManager.SHOW_IMPLICIT)
    }

    override fun onRobotFocusGained(context: QiContext?) {
        qiContext = context
        if (!greeted) {
            greeted = true
            speak("Hello! I'm here to help with a health screening. Would you like to start?") {
                questionEditText.requestFocus()
                showKeyboard()
            }
        }
    }

    override fun onRobotFocusLost() {
        qiContext = null
    }

    override fun onRobotFocusRefused(reason: String?) {
        Toast.makeText(requireContext(),
            "Focus refused: $reason", Toast.LENGTH_SHORT).show()
    }

    override fun onDestroyView() {
        QiSDK.unregister(requireActivity(), this)
        super.onDestroyView()
    }
}
