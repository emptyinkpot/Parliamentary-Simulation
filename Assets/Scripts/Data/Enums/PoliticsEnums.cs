namespace ImperialStrategy.Politics
{
    public enum BillStatus
    {
        Pending,
        Voting,
        Passed,
        Rejected
    }

    public enum Chamber
    {
        Upper,
        Lower
    }

    public enum PeerType
    {
        Lifetime,
        Meritorious,
        Imperial
    }

    public enum VoteChoice
    {
        Support,
        Oppose,
        Abstain
    }

    public enum DecreeType
    {
        Appointment,
        Dissolution,
        Emergency,
        Honor,
        Pardon,
        Administrative,
        Military,
        Diplomatic
    }

    public enum DecreeStatus
    {
        Draft,
        Active,
        Expired,
        Revoked
    }

    public enum PartyRole
    {
        Leader,
        ViceLeader,
        Secretary,
        Member
    }

    public enum CabinetPosition
    {
        PrimeMinister,
        ForeignMinister,
        FinanceMinister,
        ArmyMinister,
        NavyMinister,
        HomeMinister,
        JusticeMinister,
        EducationMinister
    }
}
