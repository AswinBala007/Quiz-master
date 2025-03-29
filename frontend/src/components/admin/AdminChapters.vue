<template>
  <div class="admin-chapters">
    <AdminNavBar />
    
    <div class="page-header">
      <h1>Chapter Management: {{ subjectName }}</h1>
      <button class="btn-back" @click="goBack">&larr; Back to Subjects</button>
    </div>
    
    <div v-if="loading" class="loading-indicator">Loading chapters...</div>
    
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else>
      <!-- Actions Bar -->
      <div class="action-bar">
        <button class="btn-primary" @click="showAddModal = true">Add New Chapter</button>
      </div>
      
      <!-- Chapters List -->
      <div v-if="chapters.length === 0" class="empty-state">
        <div class="empty-icon">📖</div>
        <h3>No Chapters Found</h3>
        <p>There are no chapters added to this subject yet. Click the "Add New Chapter" button to create one.</p>
      </div>
      
      <div v-else class="chapters-grid">
        <div v-for="chapter in chapters" :key="chapter.id" class="chapter-card">
          <div class="chapter-header">
            <h3>{{ chapter.name }}</h3>
            <div class="chapter-actions">
              <button class="btn-icon" title="Edit" @click="editChapter(chapter)">✏️</button>
              <button class="btn-icon" title="Delete" @click="confirmDelete(chapter)">🗑️</button>
            </div>
          </div>
          
          <div class="chapter-description">
            {{ chapter.description || 'No description provided' }}
          </div>
          
          <div class="chapter-footer">
            <button 
              class="btn-secondary" 
              @click="navigateToQuizzes(chapter.id)"
            >
              Manage Quizzes
            </button>
          </div>
        </div>
      </div>
      
      <!-- Add/Edit Chapter Modal -->
      <div v-if="showAddModal || showEditModal" class="modal-overlay">
        <div class="modal-container">
          <div class="modal-header">
            <h3>{{ showEditModal ? 'Edit Chapter' : 'Add New Chapter' }}</h3>
            <button class="modal-close" @click="closeModals">&times;</button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitChapterForm">
              <div class="form-group">
                <label for="chapterName">Chapter Name</label>
                <input 
                  type="text" 
                  id="chapterName" 
                  v-model="chapterForm.name" 
                  required
                  placeholder="Enter chapter name"
                />
              </div>
              
              <div class="form-group">
                <label for="chapterDescription">Description (Optional)</label>
                <textarea 
                  id="chapterDescription" 
                  v-model="chapterForm.description" 
                  rows="3"
                  placeholder="Enter chapter description"
                ></textarea>
              </div>
              
              <div class="form-actions">
                <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
                <button type="submit" class="btn-primary" :disabled="formSubmitting">
                  {{ formSubmitting ? 'Saving...' : 'Save Chapter' }}
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
              Are you sure you want to delete the chapter "{{ chapterToDelete.name }}"?<br>
              This will also delete all quizzes and questions in this chapter.
            </p>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
              <button type="button" class="btn-danger" :disabled="deleteSubmitting" @click="deleteChapter">
                {{ deleteSubmitting ? 'Deleting...' : 'Delete Chapter' }}
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
  name: 'AdminChapters',
  components: {
    AdminNavBar
  },
  data() {
    return {
      subjectId: null,
      subjectName: 'Loading...',
      chapters: [],
      loading: true,
      error: null,
      
      // Modal states
      showAddModal: false,
      showEditModal: false,
      showDeleteModal: false,
      
      // Form data
      chapterForm: {
        id: null,
        name: '',
        description: ''
      },
      formSubmitting: false,
      
      // Delete operation
      chapterToDelete: {},
      deleteSubmitting: false
    }
  },
  created() {
    this.subjectId = this.$route.params.subjectId
    this.fetchSubjectDetails()
    this.fetchChapters()
  },
  methods: {
    async fetchSubjectDetails() {
      try {
        const response = await this.$axios.get(`/admin/subjects`)
        const subject = response.data.find(s => s.id == this.subjectId)
        if (subject) {
          this.subjectName = subject.name
        }
      } catch (error) {
        console.error('Error fetching subject details:', error)
      }
    },
    
    async fetchChapters() {
      try {
        const response = await this.$axios.get(`/admin/subjects/${this.subjectId}/chapters`)
        this.chapters = response.data
      } catch (error) {
        if (error.response && error.response.status === 403) {
          this.error = 'You don\'t have permission to access this page.'
          setTimeout(() => {
            this.$router.push('/dashboard')
          }, 2000)
        } else {
          this.error = 'Failed to load chapters. Please try again.'
        }
        console.error('Error fetching chapters:', error)
      } finally {
        this.loading = false
      }
    },
    
    editChapter(chapter) {
      this.chapterForm = {
        id: chapter.id,
        name: chapter.name,
        description: chapter.description || ''
      }
      this.showEditModal = true
    },
    
    async submitChapterForm() {
      this.formSubmitting = true
      
      try {
        if (this.showEditModal) {
          // We'll need to create a custom endpoint for updating chapters
          // For now, let's assume it exists (would need to be added to backend)
          await this.$axios.put(`/admin/chapters/${this.chapterForm.id}`, {
            name: this.chapterForm.name,
            description: this.chapterForm.description
          })
          
          // Update local data
          const index = this.chapters.findIndex(c => c.id === this.chapterForm.id)
          if (index !== -1) {
            this.chapters[index].name = this.chapterForm.name
            this.chapters[index].description = this.chapterForm.description
          }
        } else {
          // Create new chapter
          const response = await this.$axios.post(`/admin/subjects/${this.subjectId}/chapters`, {
            name: this.chapterForm.name,
            description: this.chapterForm.description
          })
          
          // Add to local data
          this.chapters.push({
            id: response.data.chapter_id,
            name: this.chapterForm.name,
            description: this.chapterForm.description
          })
        }
        
        this.closeModals()
      } catch (error) {
        alert('Error saving chapter. Please try again.')
        console.error('Error saving chapter:', error)
      } finally {
        this.formSubmitting = false
      }
    },
    
    confirmDelete(chapter) {
      this.chapterToDelete = chapter
      this.showDeleteModal = true
    },
    
    async deleteChapter() {
      this.deleteSubmitting = true
      
      try {
        // We'll need to create a custom endpoint for deleting chapters
        // For now, let's assume it exists (would need to be added to backend)
        await this.$axios.delete(`/admin/chapters/${this.chapterToDelete.id}`)
        
        // Remove from local data
        this.chapters = this.chapters.filter(c => c.id !== this.chapterToDelete.id)
        
        this.closeModals()
      } catch (error) {
        alert('Error deleting chapter. Please try again.')
        console.error('Error deleting chapter:', error)
      } finally {
        this.deleteSubmitting = false
      }
    },
    
    navigateToQuizzes(chapterId) {
      this.$router.push(`/admin/chapters/${chapterId}/quizzes`)
    },
    
    closeModals() {
      this.showAddModal = false
      this.showEditModal = false
      this.showDeleteModal = false
      
      // Reset form data
      this.chapterForm = {
        id: null,
        name: '',
        description: ''
      }
      
      this.chapterToDelete = {}
    },
    
    goBack() {
      this.$router.push('/admin/subjects')
    }
  }
}
</script>

<style scoped>
.admin-chapters {
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

.chapters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.chapter-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s, box-shadow 0.3s;
}

.chapter-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.chapter-header {
  padding: 1.5rem 1.5rem 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.chapter-header h3 {
  margin: 0;
  color: #2c3e50;
}

.chapter-actions {
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

.chapter-description {
  padding: 0 1.5rem 1.5rem;
  color: #666;
  flex-grow: 1;
}

.chapter-footer {
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