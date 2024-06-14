library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity bram_ctrl_tb is
end entity;

architecture arch of bram_ctrl_tb is

  constant clk_period : time := 10 ns;
  constant num_brams : integer := 2;
  constant addr_width : integer := 32;
  constant data_width : integer := 16;

  signal clk             : std_logic := '0';
  signal rst             : std_logic;
  signal bram_index      : std_logic_vector(num_brams - 1 downto 0);
  signal addr_i          : std_logic_vector(addr_width - 1 downto 0);
  signal data_i          : std_logic_vector(data_width - 1 downto 0);
  signal re              : std_logic;
  signal we              : std_logic;
  signal data_o          : std_logic_vector(data_width - 1 downto 0);
  signal dut_start       : std_logic;
  signal dut_seq_len     : std_logic_vector(32 - 1 downto 0);
  signal dut_data_o_v    : std_logic;
  signal dut_data_out    : std_logic_vector(16 - 1 downto 0);
  signal dut_data_o_rdy  : std_logic;
  signal dut_data_i_rdy  : std_logic;
  signal dut_data_in     : std_logic_vector(16 - 1 downto 0);
  signal dut_data_i_v    : std_logic;

begin

  clk <= not clk after clk_period / 2;

  dut : entity work.bram_ctrl(behavioral)
  port map (
    clk           => clk,
    rst           => rst,
    bram_index    => bram_index,
    addr_i        => addr_i,
    data_i        => data_i,
    re            => re,
    we            => we,
    data_o        => data_o,
    dut_start     => dut_start,
    dut_seq_len   => dut_seq_len,
    dut_data_o_v  => dut_data_o_v,
    dut_data_out  => dut_data_out,
    dut_data_in   => dut_data_in,
    dut_data_i_v  => dut_data_i_v,
    dut_data_i_rdy => dut_data_i_rdy,
    dut_data_o_rdy => dut_data_o_rdy
  );

  stim : process
  begin
    rst <= '1';
    dut_start <= '0';
    wait for 10*clk_period;
    rst <= '0';
    we <= '0';
    re <= '0';

    -- write test
    wait for 10*clk_period;
    bram_index <= "01";
    we <= '1';
    write_loop : for i in 0 to 10 loop
      addr_i <= std_logic_vector(to_unsigned(i, addr_width));
      data_i <= std_logic_vector(to_unsigned(i + 10, data_width));
      wait for clk_period;
    end loop ; -- write_loop
    bram_index <= "00";
    we <= '0';
    wait for clk_period;
    bram_index <= "10";
    we <= '1';
    write_loop1 : for i in 0 to 10 loop
      addr_i <= std_logic_vector(to_unsigned(i, addr_width));
      data_i <= std_logic_vector(to_unsigned(i + 100, data_width));
      wait for clk_period;
    end loop ; -- write_loop1
    bram_index <= "00";
    we <= '0';
    wait for 10*clk_period;

    -- read test 
    bram_index <= "01";
    re <= '1';
    read_loop1 : for i in 0 to 10 loop
      addr_i <= std_logic_vector(to_unsigned(i, addr_width));
      wait for clk_period;
    end loop ; -- read_loop1
    bram_index <= "00";
    re <= '0';
    wait for 10*clk_period;

    -- test sequence execution
    dut_seq_len <= std_logic_vector(to_unsigned(10, 32));
    dut_data_o_v <= '0';
    dut_data_out <= (others => '0');
    dut_data_i_rdy <= '1';
    wait for clk_period;
    dut_start <= '1';
    wait for clk_period;
    dut_start <= '0';
    wait for 3*clk_period;
    dut_data_i_rdy <= '0';
    wait for 10*clk_period;
    dut_data_i_rdy <= '1';
    wait for 10*clk_period;
    dut_data_i_rdy <= '0';
    wait for 10*clk_period;
    dut_data_o_v <= '0';
    dut_data_out <= (others => '0');
    wait for 10*clk_period;
    dut_data_o_v <= '1';
    dut_data_out <= std_logic_vector(to_unsigned(8, 16));
    wait for clk_period;
    dut_data_o_v <= '0';
    wait for 10*clk_period;
    report "SIMULATION FINSIHED" severity failure;
  end process;

end architecture;
