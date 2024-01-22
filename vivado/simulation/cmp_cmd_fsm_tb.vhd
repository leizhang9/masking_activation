library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity cmp_cmd_fsm_tb is
end entity;

architecture arch of cmp_cmd_fsm_tb is
  constant L_g : positive := 8;
  constant D_g : positive := 2;
  constant fp_fractional_bits_g : positive := 3;

  component cmp_cmd_fsm is
    port(
    clk               : in std_logic;
    clk_slow          : in std_logic;
    rst               : in std_logic;

    -- uart
    tx_data           : out std_logic_vector(7 downto 0);
    tx_valid          : out std_ulogic;
    tx_rdy            : in std_logic;

    -- command signals
    command           : in std_logic_vector(7 downto 0);
    length            : in std_logic_vector(7 downto 0);
    payload           : in std_logic_vector(7 downto 0);
    new_cmd           : in std_logic;
    new_payload       : in std_logic;
    done              : out std_logic;

    -- dut signals
    dut_a             : out  std_ulogic_vector (L_g * D_g - 1 downto 0);
    dut_b             : out  std_ulogic_vector (L_g * D_g - 1 downto 0);
    dut_rnd           : out  std_ulogic_vector (18 * L_g * (D_g - 1) - 1 downto 0);
    dut_start         : out  std_logic;
    dut_done				  : in   std_ulogic;
    dut_c             : in   std_logic_vector (L_g * D_g - 1 downto 0);
    dut_d             : in   std_logic_vector (L_g * D_g - 1 downto 0);
    dut_trn           : in   std_logic_vector (L_g * D_g - 1 downto 0)
    );
  end component;

  constant clk_period : time := 10ns;
  constant clk_period_slow : time := clk_period * 100;
  signal clk : std_logic := '0';
  signal clk_slow : std_logic := '0';
  signal rst : std_logic;

  signal tx_data : std_logic_vector(7 downto 0);
  signal tx_valid : std_ulogic;
  signal tx_rdy : std_logic;

  -- command signals
  signal command : std_logic_vector(7 downto 0);
  signal length : std_logic_vector(7 downto 0);
  signal payload : std_logic_vector(7 downto 0);
  signal new_cmd : std_logic;
  signal new_payload : std_logic;
  signal done : std_logic;

  signal dut_done : std_logic;
  signal dut_start : std_logic;
  signal dut_a : std_ulogic_vector (L_g * D_g - 1 downto 0);
  signal dut_b : std_ulogic_vector (L_g * D_g - 1 downto 0);
  signal dut_rnd : std_ulogic_vector (18 * L_g * (D_g - 1) - 1 downto 0);

  signal dut_c : std_logic_vector (L_g * D_g - 1 downto 0);
  signal dut_d : std_logic_vector (L_g * D_g - 1 downto 0);
  signal dut_trn : std_logic_vector (L_g * D_g - 1 downto 0);

begin

  clk <= not clk after clk_period/2;
  clk_slow <= not clk_slow after clk_period_slow/2;


  dut : cmp_cmd_fsm
  port map (
    clk => clk,
    clk_slow => clk_slow,
    rst => rst,
    tx_data => tx_data,
    tx_valid => tx_valid,
    tx_rdy => tx_rdy,
    command => command,
    length => length,
    payload => payload,
    new_cmd => new_cmd,
    new_payload => new_payload,
    done => done,
    dut_done => dut_done,
    dut_start => dut_start,
    dut_a => dut_a,
    dut_b => dut_b,
    dut_c => dut_c,
    dut_d => dut_d,
    dut_rnd => dut_rnd,
    dut_trn => dut_trn
  );

  stim : process
  begin
    rst <= '1';
    command <= (others => '0');
    length <= (others => '0');
    payload <= (others => '0');
    new_cmd <= '0';
    new_payload <= '0';
    tx_rdy <= '1';
    dut_done <= '0';
    wait for 5*clk_period_slow;
    rst <= '0';
    wait for 5*clk_period;

    -- load shares
    new_cmd <= '1';
    command <= x"01";
    length <= x"04";
    wait for clk_period;
    new_cmd <= '0';
    wait for clk_period;
    new_payload <= '1';
    payload <= x"ab";
    wait for clk_period;
    new_payload <= '0';
    wait for 5*clk_period;
    new_payload <= '1';
    payload <= x"58";
    wait for clk_period;
    new_payload <= '0';
    wait for 5*clk_period;
    new_payload <= '1';
    payload <= x"11";
    wait for clk_period;
    new_payload <= '0';
    wait for 5*clk_period;
    new_payload <= '1';
    payload <= x"65";
    wait for clk_period;
    new_payload <= '0';
    wait for 10*clk_period;

    -- load randomness
    new_cmd <= '1';
    command <= x"02";
    length <= x"12";
    wait for clk_period;
    new_cmd <= '0';
    wait for clk_period;
    rnd_loop : for i in 0 to 17 loop
      new_payload <= '1';
      payload <= std_logic_vector(to_unsigned(i, 8));
      wait for clk_period;
      new_payload <= '0';
      wait for 5*clk_period;
    end loop;
    wait for 10*clk_period_slow;
    -- start dut
    new_cmd <= '1';
    command <= x"03";
    length <= x"00";
    wait for clk_period;
    new_cmd <= '0';
    wait for 10*clk_period_slow;
    dut_done <= '1';
    wait for clk_period_slow;
    dut_done <= '0';
    wait for clk_period;
    tx_rdy <= '0';
    wait for 10*clk_period;
    tx_rdy <= '1';
    wait for clk_period;

    wait;
  end process;


end architecture;
