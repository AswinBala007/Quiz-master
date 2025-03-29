<template>
  <div class="quiz-container">
    <div class="page-header">
      <h1>Quizzes</h1>
      <button class="btn-back" @click="$router.push('/subjects')">&larr; Back to Subjects</button>
    </div>
    
    <div v-if="loading" class="loading-indicator">Loading quizzes...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <div v-else-if="quizzes.length === 0" class="empty-state">
      <div class="empty-icon">📝</div>
      <h3>No quizzes available</h3>
      <p>There are currently no quizzes available for this subject. Please check back later.</p>
    </div>
    <div v-else class="quiz-grid">
      <div 
        v-for="quiz in quizzes" 
        :key="quiz.id" 
        class="quiz-card"
      >
        <div class="quiz-details">
          <div class="quiz-id">Quiz #{{ quiz.id }}</div>
          <div class="quiz-info">
            <div v-if="quiz.date" class="quiz-date">
              <span class="info-label">Date:</span> {{ formatDate(quiz.date) }}
            </div>
            <div class="quiz-duration">
              <span class="info-label">Duration:</span> {{ quiz.duration }} minutes
            </div>
          </div>
        </div>
        <button class="btn-start" @click="startQuiz(quiz.id)">
          Start Quiz
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuizList',
  data() {
    return {
      quizzes: [],
      loading: true,
      error: null
    }
  },
  computed: {
    subjectId() {
      return this.$route.params.subjectId
    }
  },
  async created() {
    await this.fetchQuizzes()
  },
  methods: {
    async fetchQuizzes() {
      try {
        const response = await this.$axios.get(`/user/quizzes/${this.subjectId}`)
        this.quizzes = response.data
      } catch (error) {
        this.error = 'Failed to load quizzes. Please try again later.'
        console.error('Error fetching quizzes:', error)
        
        if (error.response && error.response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('token')
          this.$router.push('/login')
        }
      } finally {
        this.loading = false
      }
    },
    startQuiz(quizId) {
      this.$router.push(`/quiz/${quizId}`)
    },
    formatDate(dateString) {
      if (!dateString) return 'Not scheduled'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }
  }
}
</script>

<style scoped>
.quiz-container {
  padding: 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

h1 {
  margin: 0;
  color: #2c3e50;
}

.btn-back {
  background: none;
  border: none;
  color: #42b983;
  font-weight: bold;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
}

.quiz-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.quiz-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: transform 0.3s, box-shadow 0.3s;
}

.quiz-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.quiz-details {
  margin-bottom: 1.5rem;
}

.quiz-id {
  font-size: 1.25rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.quiz-info {
  color: #666;
  font-size: 0.95rem;
}

.info-label {
  font-weight: bold;
  color: #555;
}

.quiz-date, .quiz-duration {
  margin-bottom: 0.25rem;
}

.btn-start {
  width: 100%;
  padding: 0.75rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-start:hover {
  background-color: #3aa876;
}

.loading-indicator {
  text-align: center;
  font-size: 1.2rem;
  padding: 2rem;
  color: #666;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.empty-state p {
  color: #666;
  max-width: 400px;
  margin: 0 auto;
}
</style> 