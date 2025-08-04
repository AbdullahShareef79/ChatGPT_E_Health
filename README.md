

# ChatGPT E-Health: Pepper Robot PHQ-9 Health Screening

## Overview

This project transforms the **YourBestFriendPepper** Android application to include a comprehensive **PHQ-9 mental health screening** system. The robot conducts guided health assessments using natural language processing and AI-powered analysis.

## 🎯 Key Features

### **PHQ-9 Health Screening**
- **Guided Assessment**: Conducts all 9 PHQ-9 questions sequentially
- **Voice & Text Input**: Dual input methods for accessibility
- **Real-time Progress**: Visual progress tracking with question counter
- **AI Analysis**: OpenAI GPT-4o-mini for empathetic summaries
- **Data Persistence**: Local storage of all screening sessions

### **Robot Integration**
- **QiSDK Voice Recognition**: Natural speech input processing
- **Pepper Robot Compatibility**: Designed for SoftBank Robotics Pepper
- **Multimodal Interaction**: Voice, text, and touch interactions
- **Ethical Design**: Clear disclaimers and supportive messaging

## 🛠️ Technology Stack

- **Android Studio Bumblebee 2021.1.1**
- **Kotlin** - Primary language
- **QiSDK** - Pepper robot integration
- **Room Database** - Local data persistence
- **OpenAI API** - GPT-4o-mini for analysis
- **OkHttp** - Network communication

## 📋 PHQ-9 Implementation

### Questions Covered
1. Little interest or pleasure in doing things
2. Feeling down, depressed, or hopeless
3. Trouble falling/staying asleep or sleeping too much
4. Feeling tired or having little energy
5. Poor appetite or overeating
6. Feeling bad about self/failure
7. Trouble concentrating
8. Moving/speaking slowly
9. Thoughts of self-harm

### Severity Assessment
- **0-4**: Minimal symptoms
- **5-9**: Mild symptoms
- **10-14**: Moderate symptoms
- **15-19**: Moderately severe symptoms
- **20-27**: Severe symptoms

## 🚀 Setup Instructions

### Prerequisites
1. **Android Studio Bumblebee 2021.1.1**
2. **Pepper Robot** with NAOqi 2.9
3. **OpenAI API Key** (for AI analysis)
4. **Network Connection** for API calls

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/AbdullahShareef79/ChatGPT_E_Health.git
   cd ChatGPT_E_Health
   ```

2. **Configure OpenAI API**
   - Open `app/src/main/java/com/example/pepperapp/ui/Fragments/ChatFragment.kt`
   - Replace `YOUR_OPENAI_API_KEY_HERE` with your actual OpenAI API key

3. **Connect to Pepper Robot**
   - Ensure Pepper and your device are on the same network
   - Get Pepper's IP address from the notification bar
   - Use ADB to connect: `adb connect <PEPPER_IP>:5555`

4. **Build and Deploy**
   - Open project in Android Studio
   - Select Pepper as the target device
   - Build and run the application

## 📱 Usage Flow

1. **Launch Application** on Pepper robot
2. **Select "Health Screening"** from main menu
3. **Complete 9 Questions** with voice or text input
4. **Receive AI Analysis** with severity assessment
5. **View Supportive Feedback** and guidance
6. **Session Saved** locally for research

## 🔒 Security & Privacy

- **Local Storage**: All sessions stored on device
- **No Cloud Storage**: Data remains private
- **API Key Security**: Replace placeholder with actual key
- **Ethical Design**: Clear disclaimers throughout

## 📊 Research Applications

This implementation supports research on:
- **Human-Robot Interaction** in healthcare
- **Mental Health Screening** through robotics
- **Multimodal Communication** effectiveness
- **AI-Assisted Healthcare** delivery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Project**: [YourBestFriendPepper](https://github.com/L-Hadil/PepperRobot_AI_assistant) by Hadil Ladj
- **University of Montpellier** - Research supervision
- **SoftBank Robotics** - Pepper robot platform

## 📞 Support

For questions or support, please open an issue on GitHub.

---

**Note**: This is a research project and should not be used as a substitute for professional medical diagnosis or treatment.
