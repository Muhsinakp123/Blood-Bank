// Navbar Toggle
const menuToggle = document.getElementById('menuToggle');
const navLinks = document.getElementById('navLinks');

menuToggle.addEventListener('click', () => {
  navLinks.classList.toggle('show');
});

// Scroll to Top Button
const scrollBtn = document.getElementById('scrollTopBtn');
window.addEventListener('scroll', () => {
  if (window.scrollY > 300) scrollBtn.style.display = 'block';
  else scrollBtn.style.display = 'none';
});
scrollBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// Fade-in Animation on Scroll
const fadeElements = document.querySelectorAll('.fade-in');
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add('visible');
  });
});
fadeElements.forEach(el => observer.observe(el));

// Modal Functionality
const donateBtn = document.getElementById('donateBtn');
const modal = document.getElementById('donateModal');
const closeModal = document.getElementById('closeModal');

donateBtn.onclick = () => modal.style.display = 'flex';
closeModal.onclick = () => modal.style.display = 'none';
window.onclick = (e) => { if (e.target === modal) modal.style.display = 'none'; };
