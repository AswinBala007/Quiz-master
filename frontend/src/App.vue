<template>
  <div id="app">   <!-- Navbar: Only renders if userRole is present -->
    <main>
      <router-view></router-view>
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      userRole: 'user',
    };
  },
  mounted() {
    this.userRole = localStorage.getItem('userRole');
    window.addEventListener('storage', this.syncRole); // Sync across tabs
  },
  beforeUnmount() {
    window.removeEventListener('storage', this.syncRole);
  },
  methods: {
    logout() {
      localStorage.removeItem('token');
      localStorage.removeItem('userRole');
      this.userRole = null; // Update without reload
      this.$router.push('/login');
    },
    syncRole() {
      this.userRole = localStorage.getItem('userRole');
    },
  },
};
</script>

<style scoped>
body {
  margin: 0;
  padding: 0;
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
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
