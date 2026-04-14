from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

def load_data():
    iris = load_iris()
    X = iris.data
    y = iris.target
    return X, y

def split_data(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test

def scale_data(X_train, X_test):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    return X_train, X_test

def train_model(X_train, y_train):
    model = LogisticRegression()
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    return accuracy, report

def main():
    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y)
    X_train, X_test = scale_data(X_train, X_test)
    model = train_model(X_train, y_train)
    accuracy, report = evaluate_model(model, X_test, y_test)
    print("Model Accuracy:", accuracy)
    print("Classification Report:\n", report)

if __name__ == "__main__":
    main()