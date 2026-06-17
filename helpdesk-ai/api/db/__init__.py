"""Database package."""
def init_db():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        for u in SEED_USERS:
            exists = db.query(User).filter(User.email == u["email"]).first()
            if not exists:
                db.add(User(
                    email           = u["email"],
                    nom             = u["nom"],
                    prenom          = u["prenom"],
                    hashed_password = pwd_ctx.hash(u["password"]),
                    role            = u["role"],       # ← rôle respecté
                    filiale         = u["filiale"]
                ))
        db.commit()
        print("✅ Comptes seed créés")
    finally:
        db.close()