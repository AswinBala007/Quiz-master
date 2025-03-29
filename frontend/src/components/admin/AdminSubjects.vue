<template>
  <div class="admin-subjects">
    <AdminNav />
    
    <h1>Subject Management</h1>
    
    <div v-if="loading" class="loading-indicator">Loading subjects...</div>
    
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else>
      <!-- Actions Bar -->
      <div class="action-bar">
        <button class="btn-primary" @click="showAddModal = true">Add New Subject</button>
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search subjects..." 
            @input="searchSubjects"
          />
        </div>
      </div>
      
      <!-- Subjects Table -->
      <div v-if="filteredSubjects.length === 0" class="empty-state">
        <div class="empty-icon">📚</div>
        <h3>No subjects found</h3>
        <p v-if="searchQuery">No subjects match your search query. Try a different search or clear filters.</p>
        <p v-else>There are no subjects created yet. Click the "Add New Subject" button to create one.</p>
      </div>
      
      <div v-else class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Description</th>
              <th>Chapters</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="subject in filteredSubjects" :key="subject.id">
              <td>{{ subject.id }}</td>
              <td>{{ subject.name }}</td>
              <td>{{ subject.description || '-' }}</td>
              <td>
                <button class="btn-link" @click="viewChapters(subject.id)">
                  View Chapters
                </button>
              </td>
              <td class="actions-cell">
                <button class="btn-icon" title="Edit" @click="editSubject(subject)">
                  ✏️
                </button>
                <button class="btn-icon" title="Delete" @click="confirmDelete(subject)">
                  🗑️
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Add/Edit Subject Modal -->
      <div v-if="showAddModal || showEditModal" class="modal-overlay">
        <div class="modal-container">
          <div class="modal-header">
            <h3>{{ showEditModal ? 'Edit Subject' : 'Add New Subject' }}</h3>
            <button class="modal-close" @click="closeModals">&times;</button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitSubjectForm">
              <div class="form-group">
                <label for="subjectName">Subject Name</label>
                <input 
                  type="text" 
                  id="subjectName" 
                  v-model="subjectForm.name" 
                  required
                  placeholder="Enter subject name"
                />
              </div>
              
              <div class="form-group">
                <label for="subjectDescription">Description (Optional)</label>
                <textarea 
                  id="subjectDescription" 
                  v-model="subjectForm.description" 
                  rows="3"
                  placeholder="Enter subject description"
                ></textarea>
              </div>
              
              <div class="form-actions">
                <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
                <button type="submit" class="btn-primary" :disabled="formSubmitting">
                  {{ formSubmitting ? 'Saving...' : 'Save Subject' }}
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
              Are you sure you want to delete the subject "{{ subjectToDelete.name }}"?<br>
              This will also delete all associated chapters, quizzes, and questions.
            </p>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
              <button type="button" class="btn-danger" :disabled="deleteSubmitting" @click="deleteSubject">
                {{ deleteSubmitting ? 'Deleting...' : 'Delete Subject' }}
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
  name: 'AdminSubjects',
  components: {
    AdminNav
  },
  data() {
    return {
      subjects: [],
      filteredSubjects: [],
      loading: true,
      error: null,
      searchQuery: '',
      
      // Modal states
      showAddModal: false,
      showEditModal: false,
      showDeleteModal: false,
      
      // Form data
      subjectForm: {
        id: null,
        name: '',
        description: ''
      },
      formSubmitting: false,
      
      // Delete operation
      subjectToDelete: {},
      deleteSubmitting: false
    }
  },
  created() {
    this.fetchSubjects()
  },
  methods: {
    async fetchSubjects() {
      try {
        const response = await this.$axios.get('/admin/subjects')
        this.subjects = response.data
        this.filteredSubjects = [...this.subjects]
      } catch (error) {
        if (error.response && error.response.status === 403) {
          this.error = 'You don\'t have permission to access this page.'
          setTimeout(() => {
            this.$router.push('/dashboard')
          }, 2000)
        } else {
          this.error = 'Failed to load subjects. Please try again.'
        }
        console.error('Error fetching subjects:', error)
      } finally {
        this.loading = false
      }
    },
    
    searchSubjects() {
      if (!this.searchQuery.trim()) {
        this.filteredSubjects = [...this.subjects]
      } else {
        const query = this.searchQuery.toLowerCase()
        this.filteredSubjects = this.subjects.filter(subject => 
          subject.name.toLowerCase().includes(query) || 
          (subject.description && subject.description.toLowerCase().includes(query))
        )
      }
    },
    
    editSubject(subject) {
      this.subjectForm = {
        id: subject.id,
        name: subject.name,
        description: subject.description || ''
      }
      this.showEditModal = true
    },
    
    async submitSubjectForm() {
      this.formSubmitting = true
      
      try {
        if (this.showEditModal) {
          // Update existing subject
          await this.$axios.put(`/admin/subjects/${this.subjectForm.id}`, {
            name: this.subjectForm.name,
            description: this.subjectForm.description
          })
          
          // Update local data
          const index = this.subjects.findIndex(s => s.id === this.subjectForm.id)
          if (index !== -1) {
            this.subjects[index].name = this.subjectForm.name
            this.subjects[index].description = this.subjectForm.description
          }
        } else {
          // Create new subject
          const response = await this.$axios.post('/admin/subjects', {
            name: this.subjectForm.name,
            description: this.subjectForm.description
          })
          
          // Add to local data
          this.subjects.push({
            id: response.data.subject_id,
            name: this.subjectForm.name,
            description: this.subjectForm.description
          })
        }
        
        // Update filtered list
        this.searchSubjects()
        this.closeModals()
      } catch (error) {
        alert('Error saving subject. Please try again.')
        console.error('Error saving subject:', error)
      } finally {
        this.formSubmitting = false
      }
    },
    
    confirmDelete(subject) {
      this.subjectToDelete = subject
      this.showDeleteModal = true
    },
    
    async deleteSubject() {
      this.deleteSubmitting = true
      
      try {
        await this.$axios.delete(`/admin/subjects/${this.subjectToDelete.id}`)
        
        // Remove from local data
        this.subjects = this.subjects.filter(s => s.id !== this.subjectToDelete.id)
        
        // Update filtered list
        this.searchSubjects()
        this.closeModals()
      } catch (error) {
        alert('Error deleting subject. Please try again.')
        console.error('Error deleting subject:', error)
      } finally {
        this.deleteSubmitting = false
      }
    },
    
    viewChapters(subjectId) {
      this.$router.push(`/admin/subjects/${subjectId}/chapters`)
    },
    
    closeModals() {
      this.showAddModal = false
      this.showEditModal = false
      this.showDeleteModal = false
      
      // Reset form data
      this.subjectForm = {
        id: null,
        name: '',
        description: ''
      }
      
      this.subjectToDelete = {}
    }
  }
}
</script>

<style scoped>
.admin-subjects {
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

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.search-box input {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  width: 300px;
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

.table-container {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
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

.actions-cell {
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

.btn-link {
  background: none;
  border: none;
  color: #42b983;
  cursor: pointer;
  padding: 0;
  font-weight: bold;
  text-decoration: none;
}

.btn-link:hover {
  text-decoration: underline;
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
  padding: 0.75rem 1.5rem;
  background-color: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
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