
import pandas as pd
import torch
from sentence_transformers import InputExample, SentenceTransformer, losses, util
from torch.utils.data import DataLoader


# Simulate data
def simulate_data():
    """Simulates data for profiles, applications, preferences, and job postings."""
    user_profiles_data = {
        'UserID': [1, 2, 3, 4, 5],
        'Skills': [
            ['Python', 'Data Analysis', 'SQL', 'Pandas'],
            ['Java', 'Spring Boot', 'Microservices', 'Kubernetes'],
            ['JavaScript', 'React', 'Node.js', 'HTML', 'CSS'],
            ['Python', 'Machine Learning', 'TensorFlow', 'NLP'],
            ['Project Management', 'Agile', 'Scrum', 'Communication']
        ],
        'Experience': [
            'Data Analyst at BizCorp; Python scripting for data cleaning.',
            'Senior Java Developer at FinTech Solutions; Built scalable microservices.',
            'Frontend Developer at WebDesign LLC; Developed responsive UIs with React.',
            'AI Researcher at InnovateAI; Focused on NLP models with Python.',
            'Scrum Master at AgilePro; Led multiple project teams.'
        ],
        'LocationPref': ['New York', 'Remote', 'San Francisco', 'Remote', 'London']
    }
    df_user_profiles = pd.DataFrame(user_profiles_data)

    user_applications_data = {
        'UserID': [1, 1, 2, 3, 3, 4, 4, 4, 5],
        'JobID': [101, 102, 201, 301, 302, 101, 401, 402, 501]
    }
    df_user_applications = pd.DataFrame(user_applications_data)

    user_preferences_data = {
        'UserID': [1, 2, 3, 4, 5],
        'DesiredRole': ['Data Scientist', 'Backend Engineer', 'Frontend Developer', 'Machine Learning Engineer', 'Product Manager'],
        'DesiredIndustry': [['Technology', 'Finance'], ['Finance', 'E-commerce'], ['Web Development', 'Media'], ['AI', 'Research'], ['Technology', 'SaaS']],
        'ExperienceLevelSought': ['Mid-level', 'Senior', 'Mid-level', 'Senior', 'Lead'],
        'OpenToRemote': [True, True, False, True, False]
    }
    df_user_preferences = pd.DataFrame(user_preferences_data)

    job_postings_data = {
        'JobID': [101, 102, 201, 202, 301, 302, 401, 402, 501, 502, 601, 602],
        'Title': [
            'Data Analyst Python', 'Senior Data Analyst', 'Java Backend Developer', 'Lead Java Engineer',
            'React Frontend Developer', 'UI/UX Designer', 'Machine Learning Scientist - NLP', 'AI Engineer - Computer Vision',
            'Agile Project Lead', 'Technical Product Owner', 'Entry Level Python Developer', 'Remote Python Data Engineer'
        ],
        'Description': [
            'Analyze large datasets using Python and SQL. Experience with Pandas and NumPy required. Tableau for visualization.',
            'Seeking an experienced data analyst for leading projects. Strong SQL and Python skills. Leadership experience.',
            'Develop robust backend systems using Java and Spring Boot. Knowledge of microservices and cloud platforms.',
            'Lead a team of Java developers. Architect and implement scalable solutions. Strong experience with Java, Spring.',
            'Build modern web interfaces with React and JavaScript. Collaborate with UX designers. CSS and HTML proficiency.',
            'Design user-friendly interfaces and experiences. Proficiency in Figma, Sketch. Understanding of user research.',
            'Research and develop NLP models. Python, TensorFlow, PyTorch. Publications in NLP conferences a plus.',
            'Develop computer vision algorithms. Experience with OpenCV, PyTorch. C++ and Python.',
            'Lead agile projects, facilitate scrum ceremonies, and manage project timelines. CSM certification preferred.',
            'Define product roadmap and features for a technical product. Work closely with engineering teams.',
            'Junior role for Python developer. Focus on data processing tasks. SQL knowledge needed.',
            'Fully remote role for a data engineer. Python, Spark, Airflow, and AWS cloud services experience.'
        ],
        'RequiredSkills': [
            ['Python', 'SQL', 'Pandas', 'Tableau'], ['SQL', 'Python', 'Leadership', 'Communication'],
            ['Java', 'Spring Boot', 'Microservices', 'REST APIs'], ['Java', 'Spring', 'Architecture', 'Leadership'],
            ['React', 'JavaScript', 'HTML', 'CSS', 'Git'], ['Figma', 'Sketch', 'User Research', 'UI Design'],
            ['Python', 'TensorFlow', 'PyTorch', 'NLP'], ['Python', 'OpenCV', 'PyTorch', 'C++'],
            ['Agile', 'Scrum', 'JIRA', 'Communication'], ['Product Management', 'Agile', 'Roadmap'],
            ['Python', 'SQL', 'Data Processing'], ['Python', 'Spark', 'Airflow', 'AWS', 'Data Engineering']
        ],
        'Location': ['New York', 'New York', 'Remote', 'San Francisco', 'San Francisco', 'Remote', 'Remote', 'Boston', 'London', 'New York', 'New York', 'Remote'],
        'Industry': ['Technology', 'Finance', 'Finance', 'Technology', 'Web Development', 'Design', 'AI', 'AI', 'Technology', 'SaaS', 'Finance', 'Technology'],
        'RequiredExperienceLevel': ['2+ years', '5+ years', '3+ years', '7+ years', '2+ years', '3+ years', 'PhD or 5+ years', '3+ years', '5+ years', '4+ years', 'Entry-level', '3+ years']
    }
    df_job_postings = pd.DataFrame(job_postings_data)
    return df_user_profiles, df_user_applications, df_user_preferences, df_job_postings



def user_profile_to_text(row):
    skills = ', '.join(row['Skills'])
    experience = row['Experience']
    location_pref = row['LocationPref']
    desired_role = row['DesiredRole']
    desired_industry = ', '.join(row['DesiredIndustry'])
    experience_level = row['ExperienceLevelSought']
    open_to_remote = 'Open to remote' if row['OpenToRemote'] else 'Not open to remote'
    return (f"Seeking a {experience_level} {desired_role} role in the {desired_industry} industry. "
            f"Preferred location is {location_pref}. "
            f"Key skills include {skills}. "
            f"Past experience: {experience}.")

def job_posting_to_text(row):
    title = row['Title']
    description = row['Description']
    required_skills = ', '.join(row['RequiredSkills'])
    location = row['Location']
    industry = row['Industry']
    required_experience = row['RequiredExperienceLevel']
    return (f"Job Title: {row['Title']}. Industry: {row['Industry']}. Location: {row['Location']}. "
            f"Experience Required: {row['RequiredExperienceLevel']}. "
            f"Job Description: {row['Description']}. "
            f"Required Skills: {required_skills}.")


def create_positive_pairs(user_profiles, job_postings):
    role_advantage = 10
    location_advantage = 5
    industry_advantage = 3
    skill_advantage = 2


    positive_pairs = []
    for _, user in user_profiles.iterrows():
        for _, job in job_postings.iterrows():
            score = 0
            if user['DesiredRole'] in job['Title']:
                score += role_advantage
            if any(skill in job['RequiredSkills'] for skill in user['Skills']):
                score += skill_advantage
            if user['LocationPref'] == job['Location']:
                score += location_advantage
            if job['Industry'] in user['DesiredIndustry']:
                score += industry_advantage
            if score > 12:
                positive_pairs.append(InputExample(texts=[user['ProfileText'], job['JobText']], label=1.0))
    return positive_pairs

if __name__ == "__main__":
    
    df_user_profiles, df_user_applications, df_user_preferences, df_job_postings = simulate_data()
    df_user_profiles = pd.merge(df_user_profiles, df_user_preferences, on='UserID', how='left')


    df_user_profiles['ProfileText'] = df_user_profiles.apply(user_profile_to_text, axis=1)
    df_job_postings["JobText"] = df_job_postings.apply(job_posting_to_text, axis=1)

    train_samples = create_positive_pairs(df_user_profiles, df_job_postings)
    BATCH_SIZE = 32
    EPOCH = 70
    LEARNING_RATE = 2e-5

    model = SentenceTransformer('all-MiniLM-L6-v2')
    train_examples = DataLoader(dataset=train_samples, shuffle=True, batch_size=BATCH_SIZE)

    loss = losses.MultipleNegativesRankingLoss(model=model, )

    warmup_steps = int(len(train_examples)* EPOCH * 0.1)

    model.fit(train_objectives=[(train_examples, loss)],
                epochs=EPOCH,
                warmup_steps=warmup_steps,
                output_path='job_matching_model',
                use_amp=True,
                optimizer_params={'lr': LEARNING_RATE},
                show_progress_bar=True)

    user_embedding = model.encode(df_user_profiles["ProfileText"].tolist(), convert_to_tensor=True)
    job_embedding = model.encode(df_job_postings["JobText"].tolist(), convert_to_tensor=True)

    print("\n--- Top Job Matches (Fine-Tuned Approach) ---")
    for i in range(len(df_user_profiles)):
        user_doc = df_user_profiles.iloc[i]
        print(f"\nUser {user_doc['UserID']} (Desired Role: {user_doc['DesiredRole']}), Skills: {', '.join(user_doc['Skills'])}, Location Preference: {user_doc['LocationPref']})")
        
        # Calculate cosine similarity
        cosine_scores = util.cos_sim(user_embedding[i], job_embedding)[0]
        
        # Get the top 3 best matching jobs
        top_results = cosine_scores.topk(k=3)

        for score, idx in zip(top_results[0], top_results[1]):
            id_int = int(idx)
            job_doc = df_job_postings.iloc[id_int]
            print(f"Job ID: {job_doc['JobID']}, Title: {job_doc['Title']}, Score: {score.item():.4f}")