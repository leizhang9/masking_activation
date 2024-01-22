library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity a2b_cmd_fsm_tb is
end entity;

architecture arch of a2b_cmd_fsm_tb is

  component a2b_cmd_fsm is
    port(
      clk : in std_logic;
      rst : in std_logic;

      -- uart
      tx_data : out std_logic_vector(7 downto 0);
      tx_valid : out std_ulogic;
      tx_rdy : in std_logic;

      -- command signals
      command : in std_logic_vector(7 downto 0);
      length : in std_logic_vector(7 downto 0);
      payload : in std_logic_vector(7 downto 0);
      new_cmd : in std_logic;
      new_payload : in std_logic;
      done : out std_logic;

      -- dut signals
      dut_done : in std_logic;
      dut_start : out std_logic;
      A0    : out std_logic_vector(n_bit - 1 downto 0);
      A1    : out std_logic_vector(n_bit - 1 downto 0);
      r0    : out std_logic_vector(n_bit - 1 downto 0);
      r1    : out std_logic_vector(n_bit - 1 downto 0);
      r2    : out std_logic_vector(n_bit - 2 downto 0);
      r3    : out std_logic_vector(n_bit - 2 downto 0);
      r4    : out std_logic_vector(n_bit - 2 downto 0);
      z0 : in std_logic_vector(n_bit - 1 downto 0);
      z1 : in std_logic_vector(n_bit - 1 downto 0)
    );
  end component;

  constant clk_period : time := 10ns;
  signal clk : std_logic := '0';
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
  signal A0    : std_logic_vector(n_bit - 1 downto 0);
  signal A1    : std_logic_vector(n_bit - 1 downto 0);
  signal r0    : std_logic_vector(n_bit - 1 downto 0);
  signal r1    : std_logic_vector(n_bit - 1 downto 0);
  signal r2    : std_logic_vector(n_bit - 2 downto 0);
  signal r3    : std_logic_vector(n_bit - 2 downto 0);
  signal r4    : std_logic_vector(n_bit - 2 downto 0);

  signal z0 : std_logic_vector(n_bit - 1 downto 0) := x"ee";
  signal z1 : std_logic_vector(n_bit - 1 downto 0) := x"aa";

begin

  clk <= not clk after clk_period/2;

  dut : a2b_cmd_fsm
  port map (
    clk => clk,
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
    A0 => A0,
    A1 => A1,
    r0 => r0,
    r1 => r1,
    r2 => r2,
    r3 => r3,
    r4 => r4,
    z0 => z0,
    z1 => z1
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
    wait for 5*clk_period;
    rst <= '0';
    wait for 5*clk_period;

    -- load shares
    new_cmd <= '1';
    command <= x"01";
    length <= x"02";
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

    -- load randomness
    new_cmd <= '1';
    command <= x"02";
    length <= x"05";
    wait for clk_period;
    new_cmd <= '0';
    wait for clk_period;
    new_payload <= '1';
    payload <= x"01";
    wait for clk_period;
    new_payload <= '0';
    wait for 5*clk_period;
    new_payload <= '1';
    payload <= x"02";
    wait for clk_period;
    new_payload <= '0';
    wait for 5*clk_period;
    new_payload <= '1';
    payload <= x"03";
    wait for clk_period;
    new_payload <= '0';
    wait for 5*clk_period;
    new_payload <= '1';
    payload <= x"04";
    wait for clk_period;
    new_payload <= '0';
    wait for 5*clk_period;
    new_payload <= '1';
    payload <= x"05";
    wait for clk_period;
    new_payload <= '0';
    wait for 5*clk_period;

    -- start dut
    new_cmd <= '1';
    command <= x"03";
    length <= x"00";
    wait for clk_period;
    new_cmd <= '0';
    wait for 10*clk_period;
    dut_done <= '1';
    wait for clk_period;
    dut_done <= '0';
    wait for clk_period;
    tx_rdy <= '0';
    wait for 10*clk_period;
    tx_rdy <= '1';
    wait for clk_period;

    wait;
  end process;


end architecture;
