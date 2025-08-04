# PHQ-9 Health Screening Implementation

## Overview

The `YourBestFriendPepper` app has been successfully modified to include a **PHQ-9 mental health screening** feature. This replaces the previous "Chat-GPT feedback" module with a guided health assessment system.

## Key Features

### 1. **Guided PHQ-9 Screening**
- Conducts all 9 PHQ-9 questions sequentially
- Uses natural language processing to interpret responses
- Supports both voice and text input
- Provides real-time progress tracking

### 2. **AI-Powered Analysis**
- Uses OpenAI GPT-4o-mini for generating empathetic summaries
- Provides severity assessment (minimal, mild, moderate, moderately severe, severe)
- Maintains warm, supportive tone throughout the interaction

### 3. **Data Persistence**
- Stores all screening sessions in Room database
- Tracks responses, scores, and AI-generated summaries
- Enables historical analysis and research

### 4. **User Experience**
- Progress bar and question counter
- Voice recognition using QiSDK ListenBuilder
- Text input fallback
- Ethical disclaimers and supportive messaging

## Implementation Details

### Files Modified/Created

#### New Files:
- `model/PHQ9Question.kt` - Data class for PHQ-9 questions
- `model/PHQ9Session.kt` - Room entity for session storage
- `data/Converters.kt` - Type converters for Room database
- `data/PHQ9SessionDao.kt` - Data access object for sessions

#### Modified Files:
- `ui/Fragments/ChatFragment.kt` - Complete rewrite for PHQ-9 screening
- `data/PepperDatabase.kt` - Added PHQ-9 session support
- `res/layout/fragment_chat.xml` - Added progress UI elements
- `res/layout/fragment_choose.xml` - Changed button text to "Health Screening"
- `res/navigation/nav_graph.xml` - Updated fragment label

### Database Schema

```sql
CREATE TABLE phq9_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER,
    responses TEXT, -- JSON array of scores
    totalScore INTEGER,
    severity TEXT,
    gptSummary TEXT
);
```

### PHQ-9 Questions

The implementation includes all 9 standard PHQ-9 questions:

1. Little interest or pleasure in doing things
2. Feeling down, depressed, or hopeless
3. Trouble falling/staying asleep or sleeping too much
4. Feeling tired or having little energy
5. Poor appetite or overeating
6. Feeling bad about self/failure
7. Trouble concentrating
8. Moving/speaking slowly
9. Thoughts of self-harm

### Response Scoring

- **0 points**: "Not at all"
- **1 point**: "Several days"
- **2 points**: "More than half the days"
- **3 points**: "Nearly every day"

### Severity Levels

- **0-4**: Minimal symptoms
- **5-9**: Mild symptoms
- **10-14**: Moderate symptoms
- **15-19**: Moderately severe symptoms
- **20-27**: Severe symptoms

## Usage Flow

1. **User selects "Health Screening"** from main menu
2. **Pepper explains the screening process** and ethical considerations
3. **Questions are asked one by one** with voice/text input
4. **Responses are parsed and scored** automatically
5. **AI generates empathetic summary** based on total score
6. **Session is saved** to local database
7. **User receives supportive feedback** and guidance

## Technical Requirements

### Dependencies
- Room database (already included)
- OkHttp for API calls (already included)
- Gson for JSON serialization (already included)
- QiSDK for robot interaction (already included)

### API Configuration
- Replace `YOUR_API_KEY` in `ChatFragment.kt` with actual OpenAI API key
- Ensure network connectivity for OpenAI API calls

## Ethical Considerations

- **Not a diagnosis**: Clear disclaimers throughout
- **Supportive tone**: AI responses emphasize support and encouragement
- **Professional guidance**: Always suggests consulting healthcare providers
- **Data privacy**: Sessions stored locally on device
- **Informed consent**: Users understand this is a screening tool

## Future Enhancements

1. **Multi-language support** for different regions
2. **Customizable questions** for different age groups
3. **Export functionality** for healthcare providers
4. **Trend analysis** across multiple sessions
5. **Integration with healthcare systems**

## Testing

To test the implementation:

1. Set up OpenAI API key in `ChatFragment.kt`
2. Deploy to Pepper robot or Android device
3. Navigate to "Health Screening" option
4. Complete the 9-question assessment
5. Verify database storage and AI summary generation

## Research Applications

This implementation supports the original research question:
> "How does a speech-touch bimodal interaction with the Pepper humanoid robot affect emotion-recognition and verbalization in preschoolers (3–6 years)?"

The PHQ-9 screening provides a structured way to assess emotional well-being through robot interaction, enabling quantitative analysis of the robot's effectiveness in mental health support. 