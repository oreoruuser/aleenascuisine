import { useAuth } from "../hooks/useAuth";

export const ProfilePage = () => {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <main className="page">
      <h1>Profile</h1>
      <section className="card">
        <dl className="profile-list">
          <div>
            <dt>Name</dt>
            <dd>{user.name || "Not set"}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt>Phone number</dt>
            <dd>{user.phoneNumber || "Not set"}</dd>
          </div>
        </dl>
      </section>
    </main>
  );
};
