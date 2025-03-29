<template>
  <div class="admin-quizzes">
    <AdminNav />
    
    <div class="page-header">
      <h1>Quiz Management: {{ chapterName }}</h1>
      <button class="btn-back" @click="goBack">&larr; Back to Chapters</button>
    </div>
    
    <div v-if="loading" class="loading-indicator">Loading quizzes...</div>
    
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else>
      <!-- Actions Bar -->
      <div class="action-bar">
        <button class="btn-primary" @click="showAddModal = true">Add New Quiz</button>
      </div>
      
      <!-- Quizzes List -->
      <div v-if="quizzes.length === 0" class="empty-state">
        <div class="empty-icon">📝</div>
        <h3>No Quizzes Found</h3>
        <p>There are no quizzes added to this chapter yet. Click the "Add New Quiz" button to create one.</p>
      </div>
      
      <div v-else class="quizzes-list">
        <div v-for="quiz in quizzes" :key="quiz.id" class="quiz-card">
          <div class="quiz-header">
            <div class="quiz-id">Quiz #{{ quiz.id }}</div>
            <div class="quiz-actions">
              <button class="btn-icon" title="Edit" @click="editQuiz(quiz)">✏️</button>
              <button class="btn-icon" title="Delete" @click="confirmDelete(quiz)">🗑️</button>
            </div>
          </div>
          
          <div class="quiz-content">
            <div class="quiz-detail">
              <span class="detail-label">Duration:</span> {{ quiz.time_duration }} minutes
            </div>
            <div class="quiz-detail">
              <span class="detail-label">Remarks:</span> {{ quiz.remarks || 'None' }}
            </div>
          </div>
          
          <div class="quiz-footer">
            <button 
              class="btn-secondary" 
              @click="navigateToQuestions(quiz.id)"
            >
              Manage Questions
            </button>
          </div>
        </div>
      </div>
      
      <!-- Add/Edit Quiz Modal -->
      <div v-if="showAddModal || showEditModal" class="modal-overlay">
        <div class="modal-container">
          <div class="modal-header">
            <h3>{{ showEditModal ? 'Edit Quiz' : 'Add New Quiz' }}</h3>
            <button class="modal-close" @click="closeModals">&times;</button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitQuizForm">
              <div class="form-group">
                <label for="quizDuration">Duration (minutes)</label>
                <input 
                  type="number" 
                  id="quizDuration" 
                  v-model="quizForm.time_duration" 
                  required
                  min="1"
                  max="180"
                  placeholder="Enter quiz duration in minutes"
                />
              </div>
              
              <div class="form-group">
                <label for="quizRemarks">Quiz Remarks (Optional)</label>
                <textarea 
                  id="quizRemarks" 
                  v-model="quizForm.remarks" 
                  rows="3"
                  placeholder="Enter any remarks about this quiz"
                ></textarea>
              </div>
              
              <div class="form-actions">
                <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
                <button type="submit" class="btn-primary" :disabled="formSubmitting">
                  {{ formSubmitting ? 'Saving...' : 'Save Quiz' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      
      <!-- Delete Confirmation Modal -->
      <div v-if="showDeleteModal" class="modal-overlay">
        <div class="modal-container">
          <div class="modal-header">
            <h3>Confirm Delete</h3>
            <button class="modal-close" @click="closeModals">&times;</button>
          </div>
          <div class="modal-body">
            <p>
              Are you sure you want to delete Quiz #{{ quizToDelete.id }}?<br>
              This will also delete all questions and student attempts for this quiz.
            </p>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
              <button type="button" class="btn-danger" :disabled="deleteSubmitting" @click="deleteQuiz">
                {{ deleteSubmitting ? 'Deleting...' : 'Delete Quiz' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AdminNav from './AdminNav.vue'

export default {
  name: 'AdminQuizzes',
  components: {
    AdminNav
  },
  data() {
    return {
      chapterId: null,
      chapterName: 'Loading...',
      subjectId: null,
      quizzes: [],
      loading: true,
      error: null,
      
      // Modal states
      showAddModal: false,
      showEditModal: false,
      showDeleteModal: false,
      
      // Form data
      quizForm: {
        id: null,
        time_duration: 30,
        remarks: ''
      },
      formSubmitting: false,
      
      // Delete operation
      quizToDelete: {},
      deleteSubmitting: false
    }
  },
  created() {
    this.chapterId = this.$route.params.chapterId
    this.fetchChapterDetails()
    this.fetchQuizzes()
  },
  methods: {
    async fetchChapterDetails() {
      try {
        // We need to find a way to get chapter details - might need a new endpoint in backend
        // For now let's just set a generic name
        this.chapterName = `Chapter ${this.chapterId}`
        
        // Get subject ID if available - for navigation
        const parts = this.$route.path.split('/')
        const subjectsIndex = parts.indexOf('subjects')
        if (subjectsIndex !== -1 && parts.length > subjectsIndex + 1) {
          this.subjectId = parts[subjectsIndex + 1]
        }
      } catch (error) {
        console.error('Error fetching chapter details:', error)
      }
    },
    
    async fetchQuizzes() {
      try {
        const response = await this.$axios.get(`/admin/chapters/${this.chapterId}/quizzes`)
        this.quizzes = response.data
      } catch (error) {
        if (error.response && error.response.status === 403) {
          this.error = 'You don\'t have permission to access this page.'
          setTimeout(() => {
            this.$router.push('/dashboard')
          }, 2000)
        } else {
          this.error = 'Failed to load quizzes. Please try again.'
        }
        console.error('Error fetching quizzes:', error)
      } finally {
        this.loading = false
      }
    },
    
    editQuiz(quiz) {
      this.quizForm = {
        id: quiz.id,
        time_duration: quiz.time_duration,
        remarks: quiz.remarks || ''
      }
      this.showEditModal = true
    },
    
    async submitQuizForm() {
      this.formSubmitting = true
      
      try {
        if (this.showEditModal) {
          // Update existing quiz
          await this.$axios.put(`/admin/quizzes/${this.quizForm.id}`, {
            time_duration: this.quizForm.time_duration,
            remarks: this.quizForm.remarks
          })
          
          // Update local data
          const index = this.quizzes.findIndex(q => q.id === this.quizForm.id)
          if (index !== -1) {
            this.quizzes[index].time_duration = this.quizForm.time_duration
            this.quizzes[index].remarks = this.quizForm.remarks
          }
        } else {
          // Create new quiz
          const response = await this.$axios.post(`/admin/chapters/${this.chapterId}/quizzes`, {
            time_duration: this.quizForm.time_duration,
            remarks: this.quizForm.remarks
          })
          
          // Add to local data
          this.quizzes.push({
            id: response.data.quiz_id,
            time_duration: this.quizForm.time_duration,
            remarks: this.quizForm.remarks
          })
        }
        
        this.closeModals()
      } catch (error) {
        alert('Error saving quiz. Please try again.')
        console.error('Error saving quiz:', error)
      } finally {
        this.formSubmitting = false
      }
    },
    
    confirmDelete(quiz) {
      this.quizToDelete = quiz
      this.showDeleteModal = true
    },
    
    async deleteQuiz() {
      this.deleteSubmitting = true
      
      try {
        await this.$axios.delete(`/admin/quizzes/${this.quizToDelete.id}`)
        
        // Remove from local data
        this.quizzes = this.quizzes.filter(q => q.id !== this.quizToDelete.id)
        
        this.closeModals()
      } catch (error) {
        alert('Error deleting quiz. Please try again.')
        console.error('Error deleting quiz:', error)
      } finally {
        this.deleteSubmitting = false
      }
    },
    
    navigateToQuestions(quizId) {
      this.$router.push(`/admin/quizzes/${quizId}/questions`)
    },
    
    goBack() {
      if (this.subjectId) {
        this.$router.push(`/admin/subjects/${this.subjectId}/chapters`)
      } else {
        this.$router.push('/admin/subjects')
      }
    },
    
    closeModals() {
      this.showAddModal = false
      this.showEditModal = false
      this.showDeleteModal = false
      
      // Reset form data
      this.quizForm = {
        id: null,
        time_duration: 30,
        remarks: ''
      }
      
      this.quizToDelete = {}
    }
  }
}
</script>

<style scoped>
.admin-quizzes {
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

.action-bar {
  margin-bottom: 1.5rem;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #3aa876;
}

.btn-primary:disabled {
  background-color: #93d7be;
  cursor: not-allowed;
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

.quizzes-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.quiz-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s, box-shadow 0.3s;
}

.quiz-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.quiz-header {
  padding: 1.5rem 1.5rem 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quiz-id {
  font-size: 1.25rem;
  font-weight: bold;
  color: #2c3e50;
}

.quiz-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0.25rem;
  opacity: 0.8;
}

.btn-icon:hover {
  opacity: 1;
}

.quiz-content {
  padding: 0 1.5rem 1.5rem;
  flex-grow: 1;
}

.quiz-detail {
  margin-bottom: 0.5rem;
  color: #666;
}

.detail-label {
  font-weight: bold;
  color: #555;
}

.quiz-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #eee;
  text-align: right;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background-color: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-secondary:hover {
  background-color: #e0e0e0;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-container {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  line-height: 1;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #333;
}

input, textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
}

textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-danger {
  padding: 0.75rem 1.5rem;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
}

.btn-danger:hover {
  background-color: #c0392b;
}

.btn-danger:disabled {
  background-color: #f1a9a0;
  cursor: not-allowed;
}
</style> 