<template>
  <div class="quiz-attempt-container">
    <!-- Loading state -->
    <div v-if="loading" class="loading-indicator">
      <div class="spinner"></div>
      <div>Loading quiz...</div>
    </div>
    
    <!-- Error state -->
    <div v-else-if="error" class="error-message">
      <h3>{{ error }}</h3>
      <button class="btn-back" @click="$router.push('/subjects')">Back to Subjects</button>
    </div>
    
    <!-- Quiz completed state -->
    <div v-else-if="quizCompleted" class="quiz-completed">
      <div class="result-icon">🎉</div>
      <h2>Quiz Completed!</h2>
      <div class="score-display">
        <div class="score-value">{{ score }}%</div>
        <div class="score-details">
          <div>{{ correctAnswers }} correct out of {{ totalQuestions }}</div>
        </div>
      </div>
      <div class="action-buttons">
        <button class="btn-primary" @click="$router.push('/subjects')">Take Another Quiz</button>
        <button class="btn-secondary" @click="$router.push('/history')">View History</button>
      </div>
    </div>
    
    <!-- Active quiz state -->
    <div v-else class="active-quiz">
      <div class="quiz-header">
        <h2>Quiz #{{ quizId }}</h2>
        <div class="timer" :class="{ 'timer-warning': timeRemaining < 60 }">
          Time Remaining: {{ formatTime(timeRemaining) }}
        </div>
      </div>
      
      <div class="questions-container">
        <div 
          v-for="(question, index) in questions" 
          :key="question.id" 
          class="question-card"
        >
          <div class="question-header">
            <div class="question-number">Question {{ index + 1 }} of {{ questions.length }}</div>
          </div>
          <div class="question-text">{{ question.question }}</div>
          <div class="options-list">
            <div 
              v-for="(option, optIndex) in question.options" 
              :key="optIndex"
              class="option-item"
              :class="{ 'selected': selectedAnswers[question.id] === optIndex + 1 }"
              @click="selectAnswer(question.id, optIndex + 1)"
            >
              <div class="option-marker">{{ ['A', 'B', 'C', 'D'][optIndex] }}</div>
              <div class="option-text">{{ option }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="quiz-actions">
        <button class="btn-submit" @click="submitQuiz" :disabled="isSubmitting">
          {{ isSubmitting ? 'Submitting...' : 'Submit Quiz' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuizAttempt',
  data() {
    return {
      quizId: null,
      attemptId: null,
      questions: [],
      selectedAnswers: {},
      timeRemaining: 0,
      timer: null,
      loading: true,
      error: null,
      quizCompleted: false,
      score: 0,
      correctAnswers: 0,
      totalQuestions: 0,
      isSubmitting: false
    }
  },
  computed: {
    hasAnsweredAll() {
      return Object.keys(this.selectedAnswers).length === this.questions.length
    }
  },
  async created() {
    this.quizId = this.$route.params.quizId
    await this.startQuiz()
  },
  beforeUnmount() {
    this.clearTimer()
  },
  methods: {
    async startQuiz() {
      try {
        const response = await this.$axios.post(`/user/quiz/${this.quizId}/start`)
        this.attemptId = response.data.attempt_id
        this.questions = response.data.questions
        this.timeRemaining = response.data.remaining_seconds
        
        // Start timer
        this.startTimer()
      } catch (error) {
        if (error.response) {
          this.error = error.response.data.message || 'Failed to start quiz'
        } else {
          this.error = 'Connection error. Please try again.'
        }
        console.error('Error starting quiz:', error)
      } finally {
        this.loading = false
      }
    },
    
    startTimer() {
      this.clearTimer() // Clear any existing timers
      
      this.timer = setInterval(() => {
        if (this.timeRemaining <= 0) {
          this.clearTimer()
          this.submitQuiz() // Auto-submit when time is up
          return
        }
        this.timeRemaining--
      }, 1000)
    },
    
    clearTimer() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    },
    
    selectAnswer(questionId, optionIndex) {
      this.selectedAnswers = {
        ...this.selectedAnswers,
        [questionId]: optionIndex
      }
    },
    
    async submitQuiz() {
      if (this.isSubmitting) return
      
      this.isSubmitting = true
      this.clearTimer()
      
      try {
        const response = await this.$axios.post('/user/quiz/submit', {
          attempt_id: this.attemptId,
          answers: this.selectedAnswers
        })
        
        // Handle successful submission
        this.quizCompleted = true
        this.score = response.data.score
        this.correctAnswers = response.data.correct
        this.totalQuestions = response.data.total
      } catch (error) {
        if (error.response) {
          this.error = error.response.data.message || 'Failed to submit quiz'
        } else {
          this.error = 'Connection error. Please try again.'
        }
        console.error('Error submitting quiz:', error)
      } finally {
        this.isSubmitting = false
      }
    },
    
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }
  }
}
</script>

<style scoped>
.quiz-attempt-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 1rem;
}

.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 0;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #42b983;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 2rem;
  border-radius: 8px;
  text-align: center;
}

.btn-back {
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  margin-top: 1rem;
  cursor: pointer;
}

.quiz-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  background-color: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.timer {
  font-size: 1.1rem;
  font-weight: bold;
  color: #2c3e50;
  background-color: #e9f5ef;
  padding: 0.5rem 1rem;
  border-radius: 4px;
}

.timer-warning {
  background-color: #f8d7da;
  color: #721c24;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.8; }
  100% { opacity: 1; }
}

.questions-container {
  margin-bottom: 2rem;
}

.question-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
}

.question-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.question-number {
  font-size: 0.9rem;
  color: #666;
}

.question-text {
  font-size: 1.1rem;
  font-weight: bold;
  margin-bottom: 1.5rem;
  color: #2c3e50;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-item:hover {
  background-color: #f8f9fa;
  border-color: #aaa;
}

.option-item.selected {
  background-color: #e0f7ed;
  border-color: #42b983;
}

.option-marker {
  background-color: #f0f0f0;
  color: #555;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 0.75rem;
}

.option-item.selected .option-marker {
  background-color: #42b983;
  color: white;
}

.quiz-actions {
  display: flex;
  justify-content: center;
}

.btn-submit {
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.75rem 2rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-submit:hover {
  background-color: #3aa876;
}

.btn-submit:disabled {
  background-color: #93d7be;
  cursor: not-allowed;
}

/* Quiz Completed Styles */
.quiz-completed {
  background-color: white;
  border-radius: 8px;
  padding: 3rem 2rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  text-align: center;
}

.result-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.score-display {
  margin: 2rem 0;
}

.score-value {
  font-size: 3rem;
  font-weight: bold;
  color: #42b983;
}

.score-details {
  margin-top: 0.5rem;
  color: #666;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary {
  background-color: #42b983;
  color: white;
}

.btn-primary:hover {
  background-color: #3aa876;
}

.btn-secondary {
  background-color: #f0f0f0;
  color: #333;
}

.btn-secondary:hover {
  background-color: #e0e0e0;
}
</style> 