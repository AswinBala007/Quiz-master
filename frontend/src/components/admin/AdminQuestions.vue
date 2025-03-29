<template>
  <div class="admin-questions">
    <AdminNavBar />
    
    <div class="page-header">
      <h1>Question Management: Quiz #{{ quizId }}</h1>
      <button class="btn-back" @click="goBack">&larr; Back to Quizzes</button>
    </div>
    
    <div v-if="loading" class="loading-indicator">Loading questions...</div>
    
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else>
      <!-- Actions Bar -->
      <div class="action-bar">
        <button class="btn-primary" @click="showAddModal = true">Add New Question</button>
      </div>
      
      <!-- Questions List -->
      <div v-if="questions.length === 0" class="empty-state">
        <div class="empty-icon">❓</div>
        <h3>No Questions Found</h3>
        <p>There are no questions added to this quiz yet. Click the "Add New Question" button to create one.</p>
      </div>
      
      <div v-else class="questions-list">
        <div v-for="(question, index) in questions" :key="question.id" class="question-card">
          <div class="question-number">Question {{ index + 1 }}</div>
          
          <div class="question-content">
            <div class="question-text">{{ question.text }}</div>
            
            <div class="options-list">
              <div 
                v-for="(option, optIndex) in question.options" 
                :key="optIndex" 
                :class="['option-item', { 'correct-option': optIndex === question.correct_option }]"
              >
                <div class="option-index">{{ ['A', 'B', 'C', 'D'][optIndex] }}</div>
                <div class="option-text">{{ option }}</div>
              </div>
            </div>
          </div>
          
          <div class="question-actions">
            <button class="btn-icon" title="Edit" @click="editQuestion(question)">✏️</button>
            <button class="btn-icon" title="Delete" @click="confirmDelete(question)">🗑️</button>
          </div>
        </div>
      </div>
      
      <!-- Add/Edit Question Modal -->
      <div v-if="showAddModal || showEditModal" class="modal-overlay">
        <div class="modal-container question-modal">
          <div class="modal-header">
            <h3>{{ showEditModal ? 'Edit Question' : 'Add New Question' }}</h3>
            <button class="modal-close" @click="closeModals">&times;</button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitQuestionForm">
              <div class="form-group">
                <label for="questionText">Question Text</label>
                <textarea 
                  id="questionText" 
                  v-model="questionForm.text" 
                  rows="3"
                  required
                  placeholder="Enter the question text"
                ></textarea>
              </div>
              
              <div class="form-group">
                <label>Options</label>
                <div 
                  v-for="(option, index) in questionForm.options" 
                  :key="index"
                  class="option-form-item"
                >
                  <div class="option-label">{{ ['A', 'B', 'C', 'D'][index] }}</div>
                  <input 
                    type="text" 
                    v-model="questionForm.options[index]" 
                    :placeholder="`Enter option ${['A', 'B', 'C', 'D'][index]}`"
                    required
                  />
                  <div class="option-radio">
                    <input 
                      type="radio" 
                      :id="`option${index}`" 
                      :value="index" 
                      v-model="questionForm.correct_option"
                      required
                    />
                    <label :for="`option${index}`">Correct</label>
                  </div>
                </div>
              </div>
              
              <div class="form-actions">
                <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
                <button type="submit" class="btn-primary" :disabled="formSubmitting">
                  {{ formSubmitting ? 'Saving...' : 'Save Question' }}
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
              Are you sure you want to delete this question?<br>
              This action cannot be undone.
            </p>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
              <button type="button" class="btn-danger" :disabled="deleteSubmitting" @click="deleteQuestion">
                {{ deleteSubmitting ? 'Deleting...' : 'Delete Question' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AdminNavBar from './AdminNavBar.vue'

export default {
  name: 'AdminQuestions',
  components: {
    AdminNavBar
  },
  data() {
    return {
      quizId: null,
      chapterId: null,
      questions: [],
      loading: true,
      error: null,
      
      // Modal states
      showAddModal: false,
      showEditModal: false,
      showDeleteModal: false,
      
      // Form data
      questionForm: {
        id: null,
        text: '',
        options: ['', '', '', ''],
        correct_option: null
      },
      formSubmitting: false,
      
      // Delete operation
      questionToDelete: {},
      deleteSubmitting: false
    }
  },
  created() {
    this.quizId = this.$route.params.quizId
    this.fetchQuizDetails()
    this.fetchQuestions()
  },
  methods: {
    async fetchQuizDetails() {
      try {
        // Extract chapter ID from route if available (for navigation)
        const parts = this.$route.path.split('/')
        const chaptersIndex = parts.indexOf('chapters')
        if (chaptersIndex !== -1 && parts.length > chaptersIndex + 1) {
          this.chapterId = parts[chaptersIndex + 1]
        }
      } catch (error) {
        console.error('Error fetching quiz details:', error)
      }
    },
    
    async fetchQuestions() {
      try {
        const response = await this.$axios.get(`/admin/quizzes/${this.quizId}/questions`)
        this.questions = response.data
      } catch (error) {
        if (error.response && error.response.status === 403) {
          this.error = 'You don\'t have permission to access this page.'
          setTimeout(() => {
            this.$router.push('/dashboard')
          }, 2000)
        } else {
          this.error = 'Failed to load questions. Please try again.'
        }
        console.error('Error fetching questions:', error)
      } finally {
        this.loading = false
      }
    },
    
    editQuestion(question) {
      this.questionForm = {
        id: question.id,
        text: question.text,
        options: [...question.options], // Make a copy
        correct_option: question.correct_option
      }
      this.showEditModal = true
    },
    
    async submitQuestionForm() {
      this.formSubmitting = true
      
      try {
        // Basic validation
        if (this.questionForm.text.trim() === '') {
          alert('Please enter a question text.')
          this.formSubmitting = false
          return
        }
        
        if (this.questionForm.options.some(opt => opt.trim() === '')) {
          alert('Please fill in all options.')
          this.formSubmitting = false
          return
        }
        
        if (this.questionForm.correct_option === null) {
          alert('Please select a correct option.')
          this.formSubmitting = false
          return
        }
        
        if (this.showEditModal) {
          // Update existing question
          await this.$axios.put(`/admin/questions/${this.questionForm.id}`, {
            text: this.questionForm.text,
            options: this.questionForm.options,
            correct_option: this.questionForm.correct_option
          })
          
          // Update local data
          const index = this.questions.findIndex(q => q.id === this.questionForm.id)
          if (index !== -1) {
            this.questions[index].text = this.questionForm.text
            this.questions[index].options = [...this.questionForm.options]
            this.questions[index].correct_option = this.questionForm.correct_option
          }
        } else {
          // Create new question
          const response = await this.$axios.post(`/admin/quizzes/${this.quizId}/questions`, {
            text: this.questionForm.text,
            options: this.questionForm.options,
            correct_option: this.questionForm.correct_option
          })
          
          // Add to local data
          this.questions.push({
            id: response.data.question_id,
            text: this.questionForm.text,
            options: [...this.questionForm.options],
            correct_option: this.questionForm.correct_option
          })
        }
        
        this.closeModals()
      } catch (error) {
        alert('Error saving question. Please try again.')
        console.error('Error saving question:', error)
      } finally {
        this.formSubmitting = false
      }
    },
    
    confirmDelete(question) {
      this.questionToDelete = question
      this.showDeleteModal = true
    },
    
    async deleteQuestion() {
      this.deleteSubmitting = true
      
      try {
        await this.$axios.delete(`/admin/questions/${this.questionToDelete.id}`)
        
        // Remove from local data
        this.questions = this.questions.filter(q => q.id !== this.questionToDelete.id)
        
        this.closeModals()
      } catch (error) {
        alert('Error deleting question. Please try again.')
        console.error('Error deleting question:', error)
      } finally {
        this.deleteSubmitting = false
      }
    },
    
    goBack() {
      if (this.chapterId) {
        this.$router.push(`/admin/chapters/${this.chapterId}/quizzes`)
      } else {
        // If we don't have chapter info, go to admin dashboard
        this.$router.push('/admin')
      }
    },
    
    closeModals() {
      this.showAddModal = false
      this.showEditModal = false
      this.showDeleteModal = false
      
      // Reset form data
      this.questionForm = {
        id: null,
        text: '',
        options: ['', '', '', ''],
        correct_option: null
      }
      
      this.questionToDelete = {}
    }
  }
}
</script>

<style scoped>
.admin-questions {
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

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.question-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  padding: 1.5rem;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 1.5rem;
  align-items: flex-start;
}

.question-number {
  font-weight: bold;
  color: #42b983;
  min-width: 100px;
}

.question-content {
  flex: 1;
}

.question-text {
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.options-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.option-item {
  display: flex;
  padding: 0.75rem;
  border-radius: 4px;
  background-color: #f9f9f9;
  border: 1px solid #eee;
}

.correct-option {
  background-color: #e6f7ef;
  border-color: #42b983;
}

.option-index {
  min-width: 20px;
  margin-right: 8px;
  font-weight: bold;
  color: #2c3e50;
}

.option-text {
  word-break: break-word;
}

.question-actions {
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

/* Form Styling */
.question-modal {
  width: 90%;
  max-width: 700px;
}

.option-form-item {
  display: grid;
  grid-template-columns: 30px 1fr 100px;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
}

.option-label {
  font-weight: bold;
  color: #2c3e50;
}

.option-radio {
  display: flex;
  align-items: center;
  gap: 0.5rem;
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

@media (max-width: 768px) {
  .question-card {
    grid-template-columns: 1fr;
  }
  
  .question-number {
    margin-bottom: 0.5rem;
  }
  
  .question-actions {
    margin-top: 1rem;
    justify-content: flex-end;
  }
  
  .options-list {
    grid-template-columns: 1fr;
  }
}
</style> 