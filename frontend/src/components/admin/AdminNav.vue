<!-- <template>
  <div class="admin-nav">
    <div class="admin-nav-header">
      <h2>Admin Panel</h2>
    </div>
    <div class="admin-nav-links">
      <router-link to="/admin" class="nav-link" exact>
        <span class="icon">📊</span>
        <span class="label">Dashboard</span>
      </router-link>
      
      <router-link to="/admin/subjects" class="nav-link">
        <span class="icon">📚</span>
        <span class="label">Subjects</span>
      </router-link>
      
      <router-link to="/admin/users" class="nav-link">
        <span class="icon">👥</span>
        <span class="label">Users</span>
      </router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdminNav'
}
</script>

<style scoped>
.admin-nav {
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  overflow: hidden;
  margin-bottom: 2rem;
}

.admin-nav-header {
  background-color: #2c3e50;
  padding: 1rem;
}

.admin-nav-header h2 {
  color: white;
  margin: 0;
  font-size: 1.2rem;
}

.admin-nav-links {
  display: flex;
  flex-wrap: wrap;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 1rem;
  color: #333;
  text-decoration: none;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
}

.nav-link:hover {
  background-color: #eef2f7;
}

.nav-link.router-link-active {
  border-bottom-color: #42b983;
  background-color: #eef2f7;
}

.icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

@media (max-width: 768px) {
  .admin-nav-links {
    flex-direction: column;
  }
  
  .nav-link {
    border-bottom: none;
    border-left: 3px solid transparent;
  }
  
  .nav-link.router-link-active {
    border-bottom-color: transparent;
    border-left-color: #42b983;
  }
}
</style>  -->