<template>
  <div class="dashboard-container">
    <div v-if="loading" class="loading-indicator">Loading...</div>
    <div v-else>
      <h1>Welcome, {{ user.full_name }}!</h1>
      
      <div class="dashboard-cards">
        <div class="dashboard-card" @click="$router.push('/subjects')">
          <div class="card-icon">📚</div>
          <h3>Take Quizzes</h3>
          <p>Browse subjects and take quizzes to test your knowledge</p>
        </div>
        
        <div class="dashboard-card" @click="$router.push('/history')">
          <div class="card-icon">📊</div>
          <h3>View History</h3>
          <p>Review your past quiz attempts and track your progress</p>
        </div>
        
        <div class="dashboard-card" @click="$router.push('/profile')">
          <div class="card-icon">👤</div>
          <h3>Profile</h3>
          <p>Update your personal information and account settings</p>
        </div>
      </div>
      
      <div class="dashboard-stats">
        <h2>Quick Stats</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-title">Last Login</div>
            <div class="stat-value">{{ formatDate(user.last_login) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-title">Account Created</div>
            <div class="stat-value">{{ formatDate(user.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserDashboard',
  data() {
    return {
      user: {},
      loading: true,
      error: null
    }
  },
  async created() {
    await this.fetchUserData()
  },
  methods: {
    async fetchUserData() {
      try {
        const response = await this.$axios.get('/me')
        this.user = response.data
      } catch (error) {
        this.error = 'Failed to load user data'
        console.error(error)
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
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 1rem;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.dashboard-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.dashboard-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
  text-align: center;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.card-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.dashboard-card h3 {
  margin: 0 0 0.75rem 0;
  color: #2c3e50;
}

.dashboard-card p {
  margin: 0;
  color: #666;
}

.dashboard-stats {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.dashboard-stats h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #2c3e50;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 1rem;
  text-align: center;
}

.stat-title {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: bold;
  color: #2c3e50;
}

.loading-indicator {
  text-align: center;
  font-size: 1.2rem;
  padding: 2rem;
  color: #666;
}
</style> 