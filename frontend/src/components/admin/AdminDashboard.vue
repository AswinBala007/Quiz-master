<template>
  <div class="admin-dashboard">
    <AdminNav />
    
    <h1>Admin Dashboard</h1>
    
    <div v-if="loading" class="loading-indicator">Loading dashboard data...</div>
    
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else class="dashboard-content">
      <!-- Overview statistics -->
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-icon">👤</div>
          <div class="stat-value">{{ stats.overview.total_users }}</div>
          <div class="stat-label">Total Users</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">👑</div>
          <div class="stat-value">{{ stats.overview.total_admins }}</div>
          <div class="stat-label">Admin Users</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">📚</div>
          <div class="stat-value">{{ stats.overview.total_subjects }}</div>
          <div class="stat-label">Subjects</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">📖</div>
          <div class="stat-value">{{ stats.overview.total_chapters }}</div>
          <div class="stat-label">Chapters</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">📝</div>
          <div class="stat-value">{{ stats.overview.total_quizzes }}</div>
          <div class="stat-label">Quizzes</div>
        </div>
      </div>
      
      <!-- Recent Users -->
      <div class="dashboard-panel">
        <h2>Recent Users</h2>
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in stats.recent_users" :key="user.id">
                <td>{{ user.id }}</td>
                <td>{{ user.full_name }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.joined }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="panel-footer">
          <router-link to="/admin/users" class="btn-link">View All Users →</router-link>
        </div>
      </div>
      
      <!-- Quiz Statistics -->
      <div class="dashboard-panel">
        <h2>Quiz Statistics</h2>
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Quiz ID</th>
                <th>Date</th>
                <th>Attempts</th>
                <th>Avg. Score</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="quiz in stats.quiz_statistics" :key="quiz.quiz_id">
                <td>{{ quiz.quiz_id }}</td>
                <td>{{ quiz.date || 'Not scheduled' }}</td>
                <td>{{ quiz.total_attempts }}</td>
                <td>
                  <span :class="getScoreClass(quiz.avg_score)">
                    {{ quiz.avg_score }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- Subject Statistics -->
      <div class="dashboard-panel">
        <h2>Subject Statistics</h2>
        <div class="subject-stats">
          <div v-for="subject in stats.subject_statistics" :key="subject.subject" class="subject-stat-item">
            <div class="subject-name">{{ subject.subject }}</div>
            <div class="subject-chapter-count">
              <span class="chapter-badge">{{ subject.chapters }}</span> Chapters
            </div>
          </div>
        </div>
        <div class="panel-footer">
          <router-link to="/admin/subjects" class="btn-link">Manage Subjects →</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AdminNav from './AdminNav.vue'

export default {
  name: 'AdminDashboard',
  components: {
    AdminNav
  },
  data() {
    return {
      stats: {
        overview: {
          total_users: 0,
          total_admins: 0,
          total_subjects: 0,
          total_chapters: 0,
          total_quizzes: 0
        },
        recent_users: [],
        quiz_statistics: [],
        subject_statistics: []
      },
      loading: true,
      error: null
    }
  },
  created() {
    this.fetchDashboardData()
  },
  methods: {
    async fetchDashboardData() {
      try {
        const response = await this.$axios.get('/admin/statistics')
        this.stats = response.data
      } catch (error) {
        if (error.response && error.response.status === 403) {
          this.error = 'You don\'t have permission to access this page.'
          // Redirect back to user dashboard if they're not an admin
          setTimeout(() => {
            this.$router.push('/dashboard')
          }, 2000)
        } else {
          this.error = 'Failed to load dashboard data. Please try again.'
        }
        console.error('Error fetching admin dashboard data:', error)
      } finally {
        this.loading = false
      }
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
.admin-dashboard {
  padding: 1rem;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
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

.dashboard-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  text-align: center;
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.stat-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.dashboard-panel {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #2c3e50;
  font-size: 1.5rem;
}

.table-responsive {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 1rem 0.75rem;
  border-bottom: 2px solid #eee;
  color: #555;
  font-weight: bold;
}

.data-table td {
  padding: 1rem 0.75rem;
  border-bottom: 1px solid #eee;
  color: #333;
}

.score-high {
  color: #155724;
  font-weight: bold;
}

.score-medium {
  color: #856404;
  font-weight: bold;
}

.score-low {
  color: #721c24;
  font-weight: bold;
}

.subject-stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.subject-stat-item {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 1rem;
}

.subject-name {
  font-weight: bold;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.subject-chapter-count {
  color: #666;
  font-size: 0.9rem;
}

.chapter-badge {
  background-color: #42b983;
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
}

.panel-footer {
  margin-top: 1.5rem;
  text-align: right;
}

.btn-link {
  color: #42b983;
  text-decoration: none;
  font-weight: bold;
}

.btn-link:hover {
  text-decoration: underline;
}
</style> 