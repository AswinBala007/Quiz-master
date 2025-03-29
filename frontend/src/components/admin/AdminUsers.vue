<template>
  <div class="admin-users">
    <!-- <AdminNav /> -->
    
    <div class="page-header">
      <h1>User Management</h1>
    </div>
    
    <div v-if="loading" class="loading-indicator">Loading users...</div>
    
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else>
      <!-- Filters and Search Bar -->
      <div class="filters-bar">
        <div class="search-container">
          <input 
            type="text" 
            v-model="searchQuery" 
            @input="onSearchInput"
            placeholder="Search by name, email or username" 
            class="search-input"
          />
          <span class="search-icon">🔍</span>
        </div>
        
        <div class="filters-container">
          <select v-model="roleFilter" @change="applyFilters" class="filter-select">
            <option value="all">All Roles</option>
            <option value="admin">Admin</option>
            <option value="user">Regular User</option>
          </select>
          
          <select v-model="statusFilter" @change="applyFilters" class="filter-select">
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>
      
      <!-- Users Table -->
      <div class="users-table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody v-if="filteredUsers.length === 0">
            <tr>
              <td colspan="7" class="no-results">
                <div class="empty-state">
                  <div class="empty-icon">👤</div>
                  <h3>No Users Found</h3>
                  <p>Try adjusting your search or filters.</p>
                </div>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr v-for="user in filteredUsers" :key="user.id">
              <td>{{ user.id }}</td>
              <td>{{ user.name }}</td>
              <td>{{ user.username }}</td>
              <td>{{ user.email }}</td>
              <td>
                <span :class="['role-badge', user.role === 'admin' ? 'admin-role' : 'user-role']">
                  {{ user.role }}
                </span>
              </td>
              <td>
                <span :class="['status-badge', user.active ? 'active-status' : 'inactive-status']">
                  {{ user.active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="btn-icon" title="Edit" @click="editUser(user)">✏️</button>
                <button 
                  v-if="user.id !== currentUserId" 
                  class="btn-icon" 
                  title="Toggle Status" 
                  @click="confirmToggleStatus(user)"
                >
                  {{ user.active ? '🔒' : '🔓' }}
                </button>
                <button 
                  class="btn-icon" 
                  title="Reset Password" 
                  @click="confirmResetPassword(user)"
                >
                  🔑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <div class="pagination" v-if="totalPages > 1">
        <button 
          class="pagination-btn" 
          :disabled="currentPage === 1" 
          @click="changePage(currentPage - 1)"
        >
          Previous
        </button>
        
        <div class="pagination-info">
          Page {{ currentPage }} of {{ totalPages }}
        </div>
        
        <button 
          class="pagination-btn" 
          :disabled="currentPage === totalPages" 
          @click="changePage(currentPage + 1)"
        >
          Next
        </button>
      </div>
      
      <!-- Edit User Modal -->
      <div v-if="showEditModal" class="modal-overlay">
        <div class="modal-container">
          <div class="modal-header">
            <h3>Edit User</h3>
            <button class="modal-close" @click="closeModals">&times;</button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitUserForm">
              <div class="form-group">
                <label for="userName">Name</label>
                <input 
                  type="text" 
                  id="userName" 
                  v-model="userForm.name" 
                  required
                  placeholder="Enter user's full name"
                />
              </div>
              
              <div class="form-group">
                <label for="userEmail">Email</label>
                <input 
                  type="email" 
                  id="userEmail" 
                  v-model="userForm.email" 
                  required
                  placeholder="Enter user's email"
                />
              </div>
              
              <div class="form-group">
                <label for="userRole">Role</label>
                <select 
                  id="userRole" 
                  v-model="userForm.role" 
                  required
                  :disabled="userForm.id === currentUserId"
                >
                  <option value="user">Regular User</option>
                  <option value="admin">Admin</option>
                </select>
                <div v-if="userForm.id === currentUserId" class="help-text">
                  You cannot change your own role.
                </div>
              </div>
              
              <div class="form-actions">
                <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
                <button type="submit" class="btn-primary" :disabled="formSubmitting">
                  {{ formSubmitting ? 'Saving...' : 'Save Changes' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      
      <!-- Toggle Status Confirmation Modal -->
      <div v-if="showStatusModal" class="modal-overlay">
        <div class="modal-container">
          <div class="modal-header">
            <h3>{{ userToToggle.active ? 'Deactivate User' : 'Activate User' }}</h3>
            <button class="modal-close" @click="closeModals">&times;</button>
          </div>
          <div class="modal-body">
            <p>
              Are you sure you want to {{ userToToggle.active ? 'deactivate' : 'activate' }} the user 
              <strong>{{ userToToggle.name }}</strong>?
              <br><br>
              {{ userToToggle.active ? 
                 'This will prevent them from logging in.' : 
                 'This will allow them to log in again.' }}
            </p>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeModals">Cancel</button>
              <button 
                type="button" 
                :class="userToToggle.active ? 'btn-danger' : 'btn-primary'" 
                :disabled="statusSubmitting" 
                @click="toggleUserStatus"
              >
                {{ statusSubmitting ? 'Processing...' : (userToToggle.active ? 'Deactivate User' : 'Activate User') }}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Reset Password Confirmation Modal -->
      <div v-if="showPasswordModal" class="modal-overlay">
        <div class="modal-container">
          <div class="modal-header">
            <h3>Reset Password</h3>
            <button class="modal-close" @click="closeModals">&times;</button>
          </div>
          <div class="modal-body">
            <p>
              Are you sure you want to reset the password for user 
              <strong>{{ userToReset.name }}</strong>?
              <br><br>
              A new temporary password will be generated and shown to you.
            </p>
            <div v-if="newPassword" class="new-password-container">
              <h4>New Temporary Password:</h4>
              <div class="password-display">{{ newPassword }}</div>
              <p class="password-instructions">
                Please share this temporary password with the user securely.
                They will be prompted to change it on their next login.
              </p>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeModals">
                {{ newPassword ? 'Close' : 'Cancel' }}
              </button>
              <button 
                v-if="!newPassword"
                type="button" 
                class="btn-primary" 
                :disabled="passwordSubmitting" 
                @click="resetUserPassword"
              >
                {{ passwordSubmitting ? 'Processing...' : 'Reset Password' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// import AdminNav from './AdminNav.vue'

export default {
  name: 'AdminUsers',
  // components: {
  //   AdminNav
  // },
  data() {
    return {
      users: [],
      filteredUsers: [],
      loading: true,
      error: null,
      currentUserId: null,
      
      // Pagination
      currentPage: 1,
      itemsPerPage: 10,
      totalPages: 1,
      
      // Filters
      searchQuery: '',
      searchTimeout: null,
      roleFilter: 'all',
      statusFilter: 'all',
      
      // Modal states
      showEditModal: false,
      showStatusModal: false,
      showPasswordModal: false,
      
      // Form data
      userForm: {
        id: null,
        name: '',
        email: '',
        role: 'user'
      },
      formSubmitting: false,
      
      // Status toggle
      userToToggle: {},
      statusSubmitting: false,
      
      // Password reset
      userToReset: {},
      passwordSubmitting: false,
      newPassword: null
    }
  },
  created() {
    this.getCurrentUser()
    this.fetchUsers()
  },
  methods: {
    async getCurrentUser() {
      try {
        const response = await this.$axios.get('/me')
        this.currentUserId = response.data.id
      } catch (error) {
        console.error('Error fetching current user:', error)
      }
    },
    
    async fetchUsers() {
      try {
        const response = await this.$axios.get('/admin/users')
        this.users = response.data
        this.applyFilters()
        this.calculatePagination()
      } catch (error) {
        if (error.response && error.response.status === 403) {
          this.error = 'You don\'t have permission to access this page.'
          setTimeout(() => {
            this.$router.push('/dashboard')
          }, 2000)
        } else {
          this.error = 'Failed to load users. Please try again.'
        }
        console.error('Error fetching users:', error)
      } finally {
        this.loading = false
      }
    },
    
    onSearchInput() {
      // Debounce search to avoid too many filter operations
      clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(() => {
        this.applyFilters()
      }, 300)
    },
    
    applyFilters() {
      let filtered = [...this.users]
      
      // Apply search query
      if (this.searchQuery.trim() !== '') {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(user => 
          user.name.toLowerCase().includes(query) ||
          user.email.toLowerCase().includes(query) ||
          user.username.toLowerCase().includes(query)
        )
      }
      
      // Apply role filter
      if (this.roleFilter !== 'all') {
        filtered = filtered.filter(user => user.role === this.roleFilter)
      }
      
      // Apply status filter
      if (this.statusFilter !== 'all') {
        const isActive = this.statusFilter === 'active'
        filtered = filtered.filter(user => user.active === isActive)
      }
      
      this.filteredUsers = filtered
      this.calculatePagination()
      this.currentPage = 1 // Reset to first page when filters change
    },
    
    calculatePagination() {
      this.totalPages = Math.ceil(this.filteredUsers.length / this.itemsPerPage)
      
      // Slice users for current page
      const startIndex = (this.currentPage - 1) * this.itemsPerPage
      const endIndex = startIndex + this.itemsPerPage
      this.filteredUsers = this.filteredUsers.slice(startIndex, endIndex)
    },
    
    changePage(page) {
      this.currentPage = page
      this.applyFilters()
    },
    
    editUser(user) {
      this.userForm = {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role
      }
      this.showEditModal = true
    },
    
    async submitUserForm() {
      this.formSubmitting = true
      
      try {
        await this.$axios.put(`/admin/users/${this.userForm.id}`, {
          name: this.userForm.name,
          email: this.userForm.email,
          role: this.userForm.role
        })
        
        // Update local data
        const index = this.users.findIndex(u => u.id === this.userForm.id)
        if (index !== -1) {
          this.users[index].name = this.userForm.name
          this.users[index].email = this.userForm.email
          this.users[index].role = this.userForm.role
        }
        
        this.applyFilters()
        this.closeModals()
      } catch (error) {
        alert('Error updating user. Please try again.')
        console.error('Error updating user:', error)
      } finally {
        this.formSubmitting = false
      }
    },
    
    confirmToggleStatus(user) {
      this.userToToggle = user
      this.showStatusModal = true
    },
    
    async toggleUserStatus() {
      this.statusSubmitting = true
      
      try {
        await this.$axios.put(`/admin/users/${this.userToToggle.id}/status`, {
          active: !this.userToToggle.active
        })
        
        // Update local data
        const index = this.users.findIndex(u => u.id === this.userToToggle.id)
        if (index !== -1) {
          this.users[index].active = !this.userToToggle.active
        }
        
        this.applyFilters()
        this.closeModals()
      } catch (error) {
        alert('Error updating user status. Please try again.')
        console.error('Error updating user status:', error)
      } finally {
        this.statusSubmitting = false
      }
    },
    
    confirmResetPassword(user) {
      this.userToReset = user
      this.newPassword = null
      this.showPasswordModal = true
    },
    
    async resetUserPassword() {
      this.passwordSubmitting = true
      
      try {
        const response = await this.$axios.post(`/admin/users/${this.userToReset.id}/reset-password`)
        this.newPassword = response.data.temporary_password
      } catch (error) {
        alert('Error resetting password. Please try again.')
        console.error('Error resetting password:', error)
        this.closeModals()
      } finally {
        this.passwordSubmitting = false
      }
    },
    
    closeModals() {
      this.showEditModal = false
      this.showStatusModal = false
      this.showPasswordModal = false
      
      // Reset form data
      this.userForm = {
        id: null,
        name: '',
        email: '',
        role: 'user'
      }
      
      this.userToToggle = {}
      this.userToReset = {}
      this.newPassword = null
    }
  }
}
</script>

<style scoped>
.admin-users {
  padding: 1rem;
}

.page-header {
  margin-bottom: 2rem;
}

h1 {
  margin: 0;
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

/* Filters and Search */
.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.search-container {
  position: relative;
  flex: 1;
  min-width: 250px;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1rem;
  color: #666;
}

.filters-container {
  display: flex;
  gap: 0.75rem;
}

.filter-select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  background-color: white;
}

/* Users Table */
.users-table-container {
  overflow-x: auto;
  margin-bottom: 1.5rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th,
.users-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.users-table th {
  background-color: #f9f9f9;
  font-weight: bold;
  color: #333;
}

.users-table tr:last-child td {
  border-bottom: none;
}

.no-results {
  padding: 3rem !important;
}

.empty-state {
  text-align: center;
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.empty-state p {
  color: #666;
  margin: 0;
}

.role-badge,
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
  text-transform: uppercase;
}

.admin-role {
  background-color: #e7f5ff;
  color: #1e88e5;
}

.user-role {
  background-color: #f1f8e9;
  color: #7cb342;
}

.active-status {
  background-color: #e6f7ef;
  color: #42b983;
}

.inactive-status {
  background-color: #fce8e6;
  color: #e53935;
}

.actions-cell {
  white-space: nowrap;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0.25rem;
  opacity: 0.8;
  margin-right: 0.5rem;
}

.btn-icon:hover {
  opacity: 1;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 1.5rem;
  gap: 1rem;
}

.pagination-btn {
  padding: 0.5rem 1rem;
  background-color: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.pagination-btn:hover:not(:disabled) {
  background-color: #e0e0e0;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  font-size: 0.9rem;
  color: #666;
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

.help-text {
  font-size: 0.8rem;
  color: #777;
  margin-top: 0.25rem;
}

input, textarea, select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
}

select {
  background-color: white;
}

select:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
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

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background-color: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
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

/* Password reset */
.new-password-container {
  margin: 1.5rem 0;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  border-left: 4px solid #42b983;
}

.new-password-container h4 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.password-display {
  font-family: monospace;
  font-size: 1.2rem;
  padding: 0.75rem;
  background-color: #e9ecef;
  border-radius: 4px;
  margin: 0.5rem 0;
  word-break: break-all;
  text-align: center;
}

.password-instructions {
  font-size: 0.9rem;
  color: #666;
  margin: 0.5rem 0 0 0;
}

@media (max-width: 768px) {
  .filters-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-container {
    width: 100%;
  }
  
  .filters-container {
    width: 100%;
  }
  
  .users-table th,
  .users-table td {
    padding: 0.75rem 0.5rem;
    font-size: 0.9rem;
  }
  
  .role-badge,
  .status-badge {
    padding: 0.2rem 0.4rem;
    font-size: 0.7rem;
  }
  
  .btn-icon {
    font-size: 1rem;
    padding: 0.2rem;
  }
  
  .modal-container {
    width: 95%;
  }
}
</style> 