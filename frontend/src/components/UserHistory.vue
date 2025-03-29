<template>
  <div class="history-container">
    <h1>Quiz History</h1>
    
    <div v-if="loading" class="loading-indicator">Loading your quiz history...</div>
    
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else-if="quizAttempts.length === 0" class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>No Quiz Attempts</h3>
      <p>You haven't attempted any quizzes yet. Start taking quizzes to see your history.</p>
      <button class="btn-primary" @click="$router.push('/subjects')">Take a Quiz</button>
    </div>
    
    <div v-else>
      <div class="history-stats">
        <div class="stat-card">
          <div class="stat-value">{{ quizAttempts.length }}</div>
          <div class="stat-label">Total Attempts</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-value">{{ averageScore }}%</div>
          <div class="stat-label">Average Score</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-value">{{ highestScore }}%</div>
          <div class="stat-label">Highest Score</div>
        </div>
      </div>
      
      <div class="history-table-container">
        <table class="history-table">
          <thead>
            <tr>
              <th>Quiz</th>
              <th>Subject</th>
              <th>Date</th>
              <th>Duration</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="attempt in quizAttempts" :key="attempt.id">
              <td>Quiz #{{ attempt.quiz_id }}</td>
              <td>{{ attempt.subject_name }}</td>
              <td>{{ formatDate(attempt.attempt_date) }}</td>
              <td>{{ formatDuration(attempt.duration) }}</td>
              <td>
                <div 
                  class="score-pill"
                  :class="getScoreClass(attempt.score)"
                >
                  {{ attempt.score }}%
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserHistory',
  data() {
    return {
      quizAttempts: [],
      loading: true,
      error: null
    }
  },
  computed: {
    averageScore() {
      if (this.quizAttempts.length === 0) return 0
      
      const sum = this.quizAttempts.reduce((total, attempt) => total + attempt.score, 0)
      return Math.round(sum / this.quizAttempts.length)
    },
    
    highestScore() {
      if (this.quizAttempts.length === 0) return 0
      
      return Math.max(...this.quizAttempts.map(attempt => attempt.score))
    }
  },
  async created() {
    await this.fetchHistory()
  },
  methods: {
    async fetchHistory() {
      try {
        const response = await this.$axios.get('/user/history')
        this.quizAttempts = response.data
      } catch (error) {
        this.error = 'Failed to load quiz history. Please try again later.'
        console.error('Error fetching quiz history:', error)
        
        if (error.response && error.response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('token')
          this.$router.push('/login')
        }
      } finally {
        this.loading = false
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    
    formatDuration(seconds) {
      if (!seconds) return 'N/A'
      
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      
      return `${minutes}m ${remainingSeconds}s`
    },
    
    getScoreClass(score) {
      if (score >= 80) return 'score-high'
      if (score >= 60) return 'score-medium'
      return 'score-low'
    }
  }
}
</script>

<style scoped>
.history-container {
  padding: 1rem;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.history-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #42b983;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #666;
}

.history-table-container {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  overflow-x: auto;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th {
  text-align: left;
  padding: 1rem 0.75rem;
  border-bottom: 2px solid #eee;
  color: #555;
  font-weight: bold;
}

.history-table td {
  padding: 1rem 0.75rem;
  border-bottom: 1px solid #eee;
  color: #333;
}

.score-pill {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-weight: bold;
  text-align: center;
}

.score-high {
  background-color: #d4edda;
  color: #155724;
}

.score-medium {
  background-color: #fff3cd;
  color: #856404;
}

.score-low {
  background-color: #f8d7da;
  color: #721c24;
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
  margin: 0 auto 1.5rem auto;
}

.btn-primary {
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #3aa876;
}
</style> 