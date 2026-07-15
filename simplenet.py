import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# ============================================
# 1. BASIC TENSOR OPERATIONS
# ============================================

print("=== Basic Tensors ===")
# Create tensors
x = torch.tensor([1.0, 2.0, 3.0])
y = torch.ones(3, 3)  # 3x3 tensor of ones
z = torch.randn(2, 4)  # Random normal distribution

print(f"x: {x}")
print(f"y:\n{y}")
print(f"z shape: {z.shape}")

# Basic operations
a = torch.tensor([1.0, 2.0, 3.0])
b = torch.tensor([4.0, 5.0, 6.0])
print(f"Addition: {a + b}")
print(f"Dot product: {torch.dot(a, b)}")

# ============================================
# 2. SIMPLE NEURAL NETWORK EXAMPLE
# ============================================

# Generate simple dataset (y = 2x + 1 + noise)
np.random.seed(42)
X_train = np.random.rand(100, 1).astype(np.float32) * 10
y_train = (2 * X_train + 1 + np.random.randn(100, 1).astype(np.float32) * 0.5)

# Convert to PyTorch tensors
X_train = torch.from_numpy(X_train)
y_train = torch.from_numpy(y_train)

# Define a simple neural network
class SimpleNet(nn.Module):
    def __init__(self):
        super(SimpleNet, self).__init__()
        self.fc1 = nn.Linear(1, 10)  # Input layer to hidden layer
        self.fc2 = nn.Linear(10, 1)  # Hidden layer to output
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))  # ReLU activation
        x = self.fc2(x)
        return x

# Initialize model, loss, and optimizer
model = SimpleNet()
criterion = nn.MSELoss()  # Mean Squared Error
optimizer = optim.Adam(model.parameters(), lr=0.01)

# ============================================
# 3. TRAINING LOOP
# ============================================

print("\n=== Training ===")
losses = []

for epoch in range(500):
    # Forward pass
    predictions = model(X_train)
    loss = criterion(predictions, y_train)
    
    # Backward pass
    optimizer.zero_grad()  # Clear gradients
    loss.backward()        # Compute gradients
    optimizer.step()       # Update weights
    
    losses.append(loss.item())
    
    if (epoch + 1) % 100 == 0:
        print(f'Epoch [{epoch+1}/500], Loss: {loss.item():.4f}')

# ============================================
# 4. EVALUATION
# ============================================

model.eval()  # Set to evaluation mode
with torch.no_grad():  # Disable gradient computation
    X_test = torch.linspace(0, 10, 100).reshape(-1, 1)
    y_pred = model(X_test)

# Plot results
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(losses)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss')
plt.grid(True)

plt.subplot(1, 2, 2)
plt.scatter(X_train.numpy(), y_train.numpy(), alpha=0.5, label='Training data')
plt.plot(X_test.numpy(), y_pred.numpy(), 'r-', label='Model prediction')
plt.xlabel('X')
plt.ylabel('y')
plt.title('Model Fit')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('pytorch_basics.png', dpi=150)
print("\nPlot saved as 'pytorch_basics.png'")

# ============================================
# 5. SAVING AND LOADING MODEL
# ============================================

# Save model
torch.save(model.state_dict(), 'simple_model.pth')
print("\nModel saved!")

# Load model
loaded_model = SimpleNet()
loaded_model.load_state_dict(torch.load('simple_model.pth'))
print("Model loaded successfully!")