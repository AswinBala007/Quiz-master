<template>
  <div id="app">
    <header v-if="isLoggedIn">
      <nav>
        <div class="nav-brand">Quiz Master</div>
        <div class="nav-links">
          <!-- User links -->
          <template v-if="!isAdmin">
            <router-link to="/dashboard">Dashboard</router-link>
            <router-link to="/subjects">Subjects</router-link>
            <router-link to="/history">History</router-link>
            <router-link to="/profile">Profile</router-link>
          </template>
          
          <!-- Admin links -->
          <template v-else>
            <router-link to="/admin">Admin Dashboard</router-link>
            <router-link to="/admin/subjects">Subjects</router-link>
            <router-link to="/admin/users">Users</router-link>
            <router-link to="/profile">Profile</router-link>
            <div class="admin-badge">Admin</div>
          </template>
          
          <a href="#" @click.prevent="logout">Logout</a>
        </div>
      </nav>
    </header>
    <main>
      <router-view></router-view>
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    isLoggedIn() {
      return !!localStorage.getItem('token')
    },
    isAdmin() {
      return localStorage.getItem('userRole') === 'admin'
    }
  },
  methods: {
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('userRole')
      this.$router.push('/login')
    }
  }
}
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

header {
  background-color: #2c3e50;
  color: white;
  padding: 0 1rem;
}

nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 0;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #42b983;
}

.admin-badge {
  background-color: #e74c3c;
  color: white;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: bold;
}

main {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}
</style>
