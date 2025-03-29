<template>
  <div class="dashboard-container">
    <UserNavBar/>
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
      
      <!-- Export Section -->
      <div class="dashboard-panel">
        <h2>Export Quiz History</h2>
        <p class="export-description">Download your quiz history as a CSV file for your records or analysis.</p>
        
        <div class="export-buttons">
          <button @click="triggerExport()" class="btn-export" :disabled="exporting">
            <span class="export-icon">📊</span> Export Quiz History
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
                  <th>Date</th>
                  <th>Size</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="exportFile in exports" :key="exportFile.filename">
                  <td>{{ exportFile.filename }}</td>
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
import UserNavBar from './UserNavBar.vue'
export default {
  name: 'UserDashboard',
  components: {
    UserNavBar
  },
  data() {
    return {
      user: {},
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
  async created() {
    await this.fetchUserData()
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
    },
    
    // CSV Export methods
    async fetchExports() {
      try {
        const response = await this.$axios.get('/user/exports/list')
        this.exports = response.data.exports
      } catch (error) {
        console.error('Error fetching exports:', error)
        // Don't show toast here to avoid showing on initial load
      }
    },
    
    async triggerExport() {
      this.exporting = true
      try {
        const response = await this.$axios.post('/user/exports/quiz-history/trigger')
        
        // Store task ID and start checking status
        this.currentExportTaskId = response.data.task_id
        this.exportStatus = {
          status: 'PENDING',
          taskId: this.currentExportTaskId
        }
        
        this.showToast('Quiz history export started', 'info')
        
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
        const response = await this.$axios.get(`/user/exports/status/${this.currentExportTaskId}`)
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
        const response = await this.$axios.get(`/user/exports/download/${filename}`, {
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
  margin-top: 2rem;
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

/* Export Section Styles */
.dashboard-panel {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  margin-bottom: 2rem;
}

.dashboard-panel h2 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #2c3e50;
}

.export-description {
  margin-bottom: 1.5rem;
  color: #666;
}

.export-buttons {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.btn-export {
  display: flex;
  align-items: center;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.75rem 1.25rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-export:hover {
  background-color: #218838;
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
  background-color: #007bff;
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
  background-color: #0069d9;
}

.btn-download-small {
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-download-small:hover {
  background-color: #0069d9;
}

.recent-exports h3 {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
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