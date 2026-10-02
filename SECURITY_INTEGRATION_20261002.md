# LevelUpDiag security integration

N07 now treats SecurityDiag as the application-security authority. It runs SecurityDiag S04, reads fresh evidence from `.securitydiag/latest/levels/S04/result.json`, and fails when the verdict is not PASS or when release blockers remain.
