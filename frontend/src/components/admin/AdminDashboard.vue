<template>
  <AdminNavBar/>
  <div class="admin-dashboard">
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
      
      <!-- Export Section -->
      <div class="dashboard-panel">
        <h2>Data Exports</h2>
        <p class="export-description">Generate CSV reports for user quiz statistics and performance data.</p>
        
        <div class="export-buttons">
          <button @click="triggerExport('users')" class="btn-export" :disabled="exporting">
            <span class="export-icon">📊</span> Export User Statistics
          </button>
          <button @click="triggerExport('quizzes')" class="btn-export" :disabled="exporting">
            <span class="export-icon">📈</span> Export Quiz Statistics
          </button>
        </div>
        
        <!-- Export Status -->
        <div v-if="exportStatus" class="export-status">
          <div class="status-header">
            <h3>Export Status</h3>
            <button @click="checkExportStatus" class="btn-refresh" :disabled="exporting">
              ↻ Refresh
            </button>
          </div>
          
          <div class="status-content" :class="exportStatus.status.toLowerCase()">
            <div class="status-icon">
              <span v-if="exportStatus.status === 'SUCCESS'">✅</span>
              <span v-else-if="exportStatus.status === 'PENDING' || exportStatus.status === 'PROGRESS'">⏳</span>
              <span v-else-if="exportStatus.status === 'FAILURE'">❌</span>
              <span v-else>❓</span>
            </div>
            <div class="status-details">
              <div class="status-label">{{ getStatusLabel(exportStatus.status) }}</div>
              <div v-if="exportStatus.status === 'SUCCESS'" class="status-message">
                Export completed successfully! {{ exportStatus.result?.record_count || 0 }} records exported.
                <button 
                  @click="downloadExport(exportStatus.result.filename)" 
                  class="btn-download"
                >
                  Download CSV
                </button>
              </div>
              <div v-else-if="exportStatus.status === 'PENDING'" class="status-message">
                Export job is in queue. Please wait...
              </div>
              <div v-else-if="exportStatus.status === 'PROGRESS'" class="status-message">
                {{ exportStatus.progress?.status || 'Processing...' }}
              </div>
              <div v-else-if="exportStatus.status === 'FAILURE'" class="status-message error">
                Export failed: {{ exportStatus.error || 'Unknown error' }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Recent Exports -->
        <div v-if="exports.length > 0" class="recent-exports">
          <h3>Recent Exports</h3>
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Type</th>
                  <th>Date</th>
                  <th>Size</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="exportFile in exports" :key="exportFile.filename">
                  <td>{{ exportFile.filename }}</td>
                  <td>{{ exportFile.type }}</td>
                  <td>{{ exportFile.created_at }}</td>
                  <td>{{ formatFileSize(exportFile.size_bytes) }}</td>
                  <td>
                    <button @click="downloadExport(exportFile.filename)" class="btn-download-small">
                      Download
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
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
  
  <!-- Toast Notification -->
  <div class="toast-container" v-if="toast.show">
    <div class="toast" :class="toast.type">
      <div class="toast-content">
        <span class="toast-icon">
          {{ toast.type === 'success' ? '✅' : toast.type === 'error' ? '❌' : 'ℹ️' }}
        </span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>
      <button class="toast-close" @click="closeToast">×</button>
    </div>
  </div>
</template>

<script>
import AdminNavBar from './AdminNavBar.vue';

export default {
  name: 'AdminDashboard',
  components: {
    AdminNavBar
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
      error: null,
      
      // Export-related data
      exports: [],
      currentExportTaskId: null,
      exporting: false,
      exportStatus: null,
      exportStatusInterval: null,
      
      // Toast notification
      toast: {
        show: false,
        message: '',
        type: 'info', // 'success', 'error', 'info'
        timeout: null
      }
    }
  },
  created() {
    this.fetchDashboardData()
    this.fetchExports()
  },
  beforeUnmount() {
    // Clear any intervals when component is destroyed
    if (this.exportStatusInterval) {
      clearInterval(this.exportStatusInterval)
    }
    if (this.toast.timeout) {
      clearTimeout(this.toast.timeout)
    }
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
    
    // CSV Export methods
    async fetchExports() {
      try {
        const response = await this.$axios.get('/admin/exports/list')
        this.exports = response.data.exports
      } catch (error) {
        console.error('Error fetching exports:', error)
        this.showToast('Failed to load exports list', 'error')
      }
    },
    
    async triggerExport(type) {
      this.exporting = true
      try {
        const endpoint = type === 'users' ? '/admin/exports/users/trigger' : '/admin/exports/quizzes/trigger'
        const response = await this.$axios.post(endpoint)
        
        // Store task ID and start checking status
        this.currentExportTaskId = response.data.task_id
        this.exportStatus = {
          status: 'PENDING',
          taskId: this.currentExportTaskId
        }
        
        this.showToast(`${type === 'users' ? 'User' : 'Quiz'} export started`, 'info')
        
        // Start polling for status
        this.startStatusPolling()
      } catch (error) {
        console.error('Error triggering export:', error)
        this.showToast('Failed to start export job', 'error')
      } finally {
        this.exporting = false
      }
    },
    
    startStatusPolling() {
      // Clear any existing interval
      if (this.exportStatusInterval) {
        clearInterval(this.exportStatusInterval)
      }
      
      // Set up polling (check status every 2 seconds)
      this.exportStatusInterval = setInterval(this.checkExportStatus, 2000)
      
      // Stop polling after 2 minutes (to prevent endless polling)
      setTimeout(() => {
        if (this.exportStatusInterval) {
          clearInterval(this.exportStatusInterval)
          this.exportStatusInterval = null
          
          // If we're still not done, show a message
          if (this.exportStatus && ['PENDING', 'PROGRESS'].includes(this.exportStatus.status)) {
            this.showToast('Export is taking longer than expected. Please check back later.', 'info')
          }
        }
      }, 120000) // 2 minutes
    },
    
    async checkExportStatus() {
      if (!this.currentExportTaskId) return
      
      try {
        const response = await this.$axios.get(`/admin/exports/status/${this.currentExportTaskId}`)
        this.exportStatus = response.data
        
        // If completed (success or failure), stop polling and update exports list
        if (['SUCCESS', 'FAILURE'].includes(response.data.status)) {
          if (this.exportStatusInterval) {
            clearInterval(this.exportStatusInterval)
            this.exportStatusInterval = null
          }
          
          if (response.data.status === 'SUCCESS') {
            this.showToast('Export completed successfully!', 'success')
            this.fetchExports() // Refresh exports list
          } else {
            this.showToast(`Export failed: ${response.data.error || 'Unknown error'}`, 'error')
          }
        }
      } catch (error) {
        console.error('Error checking export status:', error)
        // Don't show toast for every status check error
      }
    },
    
    async downloadExport(filename) {
      try {
        // Use axios to get the file as a blob
        const response = await this.$axios.get(`/admin/exports/download/${filename}`, {
          responseType: 'blob'
        })
        
        // Create a download link
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        
        // Clean up
        window.URL.revokeObjectURL(url)
        document.body.removeChild(link)
        
        this.showToast('Download started', 'success')
      } catch (error) {
        console.error('Error downloading export:', error)
        this.showToast('Failed to download file', 'error')
      }
    },
    
    // Toast notification
    showToast(message, type = 'info') {
      // Clear existing timeout
      if (this.toast.timeout) {
        clearTimeout(this.toast.timeout)
      }
      
      // Show toast
      this.toast.message = message
      this.toast.type = type
      this.toast.show = true
      
      // Auto-hide after 5 seconds
      this.toast.timeout = setTimeout(() => {
        this.closeToast()
      }, 5000)
    },
    
    closeToast() {
      this.toast.show = false
    },
    
    // Utility methods
    getScoreClass(score) {
      if (score >= 80) return 'score-high'
      if (score >= 60) return 'score-medium'
      return 'score-low'
    },
    
    getStatusLabel(status) {
      switch (status) {
        case 'SUCCESS': return 'Completed'
        case 'FAILURE': return 'Failed'
        case 'PENDING': return 'Queued'
        case 'PROGRESS': return 'In Progress'
        default: return 'Unknown'
      }
    },
    
    formatFileSize(bytes) {
      if (bytes < 1024) return `${bytes} B`
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    },
    
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('userRole')
      this.$router.push('/login')
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

.dashboard-panel h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #2c3e50;
}

.table-responsive {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
}

.data-table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.panel-footer {
  margin-top: 1rem;
  text-align: right;
}

.btn-link {
  color: #007bff;
  text-decoration: none;
}

.btn-link:hover {
  text-decoration: underline;
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
}

.chapter-badge {
  background-color: #6c757d;
  color: white;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.score-high {
  color: #28a745;
  font-weight: bold;
}

.score-medium {
  color: #ffc107;
  font-weight: bold;
}

.score-low {
  color: #dc3545;
  font-weight: bold;
}

/* Export Section Styles */
.export-description {
  margin-bottom: 1.5rem;
  color: #666;
}

.export-buttons {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.btn-export {
  display: flex;
  align-items: center;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.75rem 1.25rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-export:hover {
  background-color: #0069d9;
}

.btn-export:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.export-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

.export-status {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.status-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.btn-refresh {
  background-color: transparent;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-refresh:hover {
  background-color: #f1f1f1;
}

.status-content {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border-radius: 4px;
}

.status-content.success {
  background-color: #d4edda;
}

.status-content.pending,
.status-content.progress {
  background-color: #fff3cd;
}

.status-content.failure {
  background-color: #f8d7da;
}

.status-icon {
  font-size: 1.5rem;
  margin-right: 1rem;
}

.status-details {
  flex: 1;
}

.status-label {
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.status-message {
  font-size: 0.9rem;
}

.status-message.error {
  color: #721c24;
}

.btn-download {
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 0.75rem;
  margin-left: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-download:hover {
  background-color: #218838;
}

.btn-download-small {
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-download-small:hover {
  background-color: #218838;
}

.recent-exports h3 {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

/* Toast Notification */
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
}

.toast {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 250px;
  max-width: 350px;
  animation: slideIn 0.3s ease;
}

.toast.success {
  background-color: #d4edda;
  color: #155724;
}

.toast.error {
  background-color: #f8d7da;
  color: #721c24;
}

.toast.info {
  background-color: #cce5ff;
  color: #004085;
}

.toast-content {
  display: flex;
  align-items: center;
}

.toast-icon {
  margin-right: 0.75rem;
}

.toast-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  opacity: 0.7;
}

.toast-close:hover {
  opacity: 1;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style> 