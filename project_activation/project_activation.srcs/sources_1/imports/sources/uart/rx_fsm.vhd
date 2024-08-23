library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity rx_fsm is
  port (
    clk : in std_logic;
    rst : in std_logic;

    -- uart
    rx_data : in std_logic_vector(7 downto 0);
    rx_valid : in std_ulogic;

    command : out std_logic_vector(7 downto 0);
    length : out std_logic_vector(7 downto 0);
    payload : out std_logic_vector(7 downto 0);
    new_cmd : out std_logic;
    new_payload : out std_logic
  );
end entity;

architecture behavioral of rx_fsm is

  type states is (reset, idle, rx_cmd, rx_len, rx_d, wait_proc);
  signal c_state : states;
  signal n_state : states;

  signal int_rst : std_logic;

  -- command signals
  signal cmd : natural range 0 to 255;
  signal cmd_valid : std_logic;
  signal cmd_en : std_logic;

  -- length signals
  signal len : natural range 0 to 255;
  signal len_valid : std_logic;
  signal len_en : std_logic;

  -- data signals
  signal data : unsigned(7 downto 0);
  signal data_valid : std_logic;
  signal data_en : std_logic;
  signal data_cnt : natural range 0 to 255;

begin

  new_payload <= data_valid;
  command <= std_logic_vector(to_unsigned(cmd, 8));
  length <= std_logic_vector(to_unsigned(len, 8));
  payload <= std_logic_vector(data);

  counter : process(clk)
  begin
    if clk'event and clk = '1' then
      if int_rst = '1' then
        data_cnt <= 0;
      elsif c_state = rx_d then
        data_cnt <= data_cnt + 1;
      end if;
    end if;

  end process;

  data_reg : process(clk)
  begin
    if clk'event and clk='1' then
      data_valid <= '0';
      if int_rst = '1' then
        data <= (others => '0');
        data_valid <= '0';
      elsif data_en = '1' then
        data <= unsigned(rx_data);
        data_valid <= '1';
      end if;
    end if;
  end process;

  len_reg : process(clk)
  begin
    if clk'event and clk='1' then
      new_cmd <= '0';
      if int_rst = '1' then
        len <= 0;
        len_valid <= '0';
      elsif len_en = '1' then
        len <= to_integer(unsigned(rx_data));
        len_valid <= '1';
        new_cmd <= '1';
      end if;
    end if;
  end process;

  cmd_reg : process(clk)
  begin
    if clk'event and clk='1' then
      if int_rst = '1' then
        cmd <= 0;
        cmd_valid <= '0';
      elsif cmd_en = '1' then
        cmd <= to_integer(unsigned(rx_data));
        cmd_valid <= '1';
      end if;
    end if;
  end process;

  next_state_logic : process(c_state, rx_valid, data_cnt, len, rst, cmd_valid, len_valid)
  begin
    case( c_state ) is
      when reset =>
        if rst = '1' then
          n_state <= reset;
        else
          n_state <= idle;
        end if;
      when idle =>
        if rx_valid = '1' then
          if cmd_valid = '0' then
            n_state <= rx_cmd;
          elsif len_valid = '0' then
            n_state <= rx_len;
          else
            n_state <= rx_d;
          end if;
        elsif data_cnt >= len and data_cnt > 0 then
          n_state <= wait_proc;
        else
          n_state <= idle;
        end if;
      when wait_proc =>
        n_state <= wait_proc;
      when others =>
        n_state <= idle;
    end case;
  end process;

  out_logic : process(c_state)
  begin
    int_rst <= '0';
    cmd_en <= '0';
    len_en <= '0';
    data_en <= '0';
    case( c_state ) is
      when reset =>
        int_rst <= '1';
      when rx_cmd =>
        cmd_en <= '1';
      when rx_len =>
        len_en <= '1';
      when rx_d =>
        data_en <= '1';
      when others =>
        int_rst <= '0';
    end case;
  end process;

  state_mem : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        c_state <= reset;
      else
        c_state <= n_state;
      end if;
    end if;
  end process;

end architecture;
